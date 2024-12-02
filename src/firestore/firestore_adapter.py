import datetime
from firebase_admin import firestore

class FirestoreAdapter:

    def __init__(self):
        pass

    def set_pending_action(self, db, user_id: str, action_data: dict):
        doc_ref = db.collection('userIds').document(user_id)
        doc_ref.set({'pending_action': action_data}, merge=True)

    def get_pending_action(self, db, user_id: str) -> dict:
        doc_ref = db.collection('userIds').document(user_id)
        doc = doc_ref.get()
        if doc.exists and 'pending_action' in doc.to_dict():
            return doc.to_dict()['pending_action']
        else:
            return None

    def clear_pending_action(self, db, user_id: str):
        doc_ref = db.collection('userIds').document(user_id)
        doc_ref.update({'pending_action': firestore.DELETE_FIELD})

    def set_sub_status(self, db, user_id, current_status, next_status=None, plan_change_date=None,pending_action=None):
        data = {
            "current_sub_status": current_status,
            "pending_action": pending_action
        }
        if next_status:
            data["next_sub_status"] = next_status
        if plan_change_date:
            # タイムゾーン情報を含めて ISO フォーマットに変換
            data["plan_change_date"] = plan_change_date.isoformat()
        ref_userIds = db.collection('userIds').document(user_id)
        ref_userIds.set(data, merge=True)

    def get_sub_status(self, db, user_id):
        ref_userIds = db.collection('userIds').document(user_id)
        doc = ref_userIds.get()
        if doc.exists:
            data = doc.to_dict()
            current_sub_status = data.get('current_sub_status', 'free')
            next_sub_status = data.get('next_sub_status')
            plan_change_date_str = data.get('plan_change_date')

            if plan_change_date_str and next_sub_status:
                # plan_change_date を日時オブジェクトに変換（タイムゾーン付き）
                plan_change_date = datetime.datetime.fromisoformat(plan_change_date_str)
                now = datetime.datetime.now(datetime.timezone.utc)

                if now >= plan_change_date:
                    # current_sub_status を更新
                    current_sub_status = next_sub_status
                    # next_sub_status と plan_change_date を削除
                    update_data = {
                        'current_sub_status': current_sub_status,
                        'next_sub_status': firestore.DELETE_FIELD,
                        'plan_change_date': firestore.DELETE_FIELD
                    }
                    ref_userIds.update(update_data)
                    next_sub_status = None
                    plan_change_date_str = None

            return {
                "current_sub_status": current_sub_status,
                "next_sub_status": next_sub_status,
                "plan_change_date": plan_change_date_str
            }
        else:
            # 初回アクセス時の初期データを設定
            data = {
                "current_sub_status": "free"
            }
            ref_userIds.set(data)
            return {
                "current_sub_status": "free",
                "next_sub_status": None,
                "plan_change_date": None
            }

    def set_botType(self, db, userId, botType):
        data = {
            "botType": botType
        }
        # userIdsコレクション内のユーザーIDドキュメントの参照を取得
        ref_userIds = db.collection('userIds').document(userId)
        # userIdsコレクションでユーザーIDとbotTypeを更新
        ref_userIds.set(data, merge=True)
    
    def get_botType(self, db, userId):
        ref_userIds = db.collection('userIds').document(userId)
        doc = ref_userIds.get()
        if doc.exists:
            return doc.to_dict().get('botType')
        else:
            data = {
                "botType": "fr"
            }
            ref_userIds.set(data, merge=True)
            return "fr"

    def update_history(self, db, userId, speaker, message, data_limit):
        new_message = {
            "timestamp": datetime.datetime.now().isoformat(),
            "speaker": speaker,
            "content": message
        }
        userIds_ref = db.collection('userIds').document(userId)
        conversations_ref = userIds_ref.collection('conversations')

        # ユーザードキュメントが存在しない場合は初期化
        if not userIds_ref.get().exists:
            self.initialize_user_data(db, userId)

        # conversationsサブコレクションに新しいメッセージを追加
        conversations_ref.add(new_message)

        # メッセージを timestamp の降順で取得
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).get()

        # メッセージの総数が指定数を超える場合、古いメッセージを削除
        if len(snapshots) > data_limit:
            # 20件目以降のメッセージを取得（古いメッセージ）
            messages_to_delete = snapshots[data_limit:]
            # 古いメッセージを削除
            for snapshot in messages_to_delete:
                snapshot.reference.delete()

    def get_history(self, db, userId, data_limit):
        conversations_ref = db.collection('userIds').document(userId).collection('conversations')
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(data_limit).get()
        messages = [snapshot.to_dict() for snapshot in snapshots]
        return messages

    def get_user_data(self, db, user_id, data_limit):
        """
        指定した user_id に紐づくすべてのデータを取得します。
        """
        user_ref = db.collection('userIds').document(user_id)
        doc = user_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            # conversations サブコレクションのデータを取得
            conversations_ref = user_ref.collection('conversations')
            snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(data_limit).get()
            conversations = [snapshot.to_dict() for snapshot in snapshots]
            user_data['conversations'] = conversations
            return user_data
        else:
            # ユーザーデータが存在しない場合は初期化する
            self.initialize_user_data(db, user_id)
            return {
                "created_at": datetime.datetime.now().isoformat(),
                "current_sub_status": "free",
                "next_sub_status": None,
                "plan_change_date": None,
                "botType": "fr",
                "pending_action": None,
                "conversations": []
            }

    def initialize_user_data(self, db, user_id):
        """
        指定した user_id の完全なデータ構造を初期化します。
        既に存在するフィールドは上書きされません。
        """
        initial_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "current_sub_status": "free",
            "next_sub_status": None,
            "plan_change_date": None,
            "botType": "fr",
            "pending_action": None,
            # 他に初期化したいフィールドがあればここに追加
        }

        user_ref = db.collection('userIds').document(user_id)
        # 既存のデータを上書きしないように merge=True を指定
        user_ref.set(initial_data, merge=True)