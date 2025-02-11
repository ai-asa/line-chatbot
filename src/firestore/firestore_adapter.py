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

    def set_new_sub(self, db, user_id, botType, new_status=None, pending_action=None):
        """
        ・トライアルプランからの切り替え対応
        / 現在のプランを取得し、トライアルプランの場合はisTrialValidをFalseにする
        ・current_sub_status、botType、pending_actionを更新する
        """
        user_ref = db.collection('userIds').document(user_id)
        data = {
            "current_sub_status": new_status,
            "pending_action": pending_action,
            "isTrialValid": True,
            "botType": botType
        }
        
        # 現在トライアルプランの場合の処理
        doc = user_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            current_sub_status = user_data.get('current_sub_status', 'free')
            if current_sub_status == 'try':
                data['isTrialValid'] = False
                
        # 同じリファレンスを使用して保存
        user_ref.set(data, merge=True)

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
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
        サブステータスのチェックと更新（get_sub_status の処理）も含めています。
        """
        user_ref = db.collection('userIds').document(user_id)
        doc = user_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            update_data = {}  # 更新データを格納する辞書
            
            # トライアル期限チェック処理
            current_sub_status = user_data.get('current_sub_status','free')
            is_trial_valid = user_data.get('isTrialValid', True)
            trial_end_str = user_data.get('trial_end')
            next_sub_status = user_data.get('next_sub_status')
            plan_change_date_str = user_data.get('plan_change_date')
            now = datetime.datetime.now(datetime.timezone.utc)
            if trial_end_str and  current_sub_status == 'try' and is_trial_valid:
                trial_end = datetime.datetime.fromisoformat(trial_end_str)
                if  now >= trial_end:
                    update_data.update({
                        'current_sub_status': 'free',
                        'isTrialValid': False
                    })
                    user_data['current_sub_status'] = 'free'
                    user_data['isTrialValid'] = False
            
            if plan_change_date_str and next_sub_status:
                plan_change_date = datetime.datetime.fromisoformat(plan_change_date_str)
                if now >= plan_change_date:
                    update_data.update({
                        'current_sub_status': next_sub_status,
                        'next_sub_status': firestore.DELETE_FIELD,
                        'plan_change_date': firestore.DELETE_FIELD
                    })
                    user_data['current_sub_status'] = next_sub_status
                    user_data.pop('next_sub_status', None)
                    user_data.pop('plan_change_date', None)
            
            # 更新が必要な場合のみ実行
            if update_data:
                user_ref.update(update_data)
            
            # conversations サブコレクションのデータ取得
            conversations_ref = user_ref.collection('conversations')
            snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(data_limit).get()
            conversations = [snapshot.to_dict() for snapshot in snapshots]
            user_data['conversations'] = conversations
            
            return user_data
        else:
            # ユーザーデータが存在しない場合は初期化する
            self.initialize_user_data(db, user_id)
            return {
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "current_sub_status": "free",
                "next_sub_status": None,
                "plan_change_date": None,
                "botType": "fr",
                "pending_action": None,
                "trial_start": None,
                "trial_end": None,
                "isTrialValid": True,
                "conversations": []
            }

    def initialize_user_data(self, db, user_id):
        """
        指定した user_id の完全なデータ構造を初期化します。
        既に存在するフィールドは上書きされません。
        """
        initial_data = {
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "current_sub_status": "free",
            "next_sub_status": None,
            "plan_change_date": None,
            "botType": "fr",
            "pending_action": None,
            "trial_start": None,
            "trial_end": None,
            "isTrialValid": True,
            "conversations": []
        }

        user_ref = db.collection('userIds').document(user_id)
        # 既存のデータを上書きしないように merge=True を指定
        user_ref.set(initial_data, merge=True)

    def set_trial_period(self, db, user_id):
        """
        ユーザーのトライアル期間を設定します。
        trial_start に現在時刻を、trial_end に1週間後の時刻を設定します。
        データベースにはUTCで保存し、戻り値はJST形式で返します。
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        trial_end = now + datetime.timedelta(weeks=1)
        
        # データベース保存用のデータ（UTC）
        data = {
            "current_sub_status": "try",
            "pending_action": None,
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat()
        }
        
        user_ref = db.collection('userIds').document(user_id)
        user_ref.set(data, merge=True)

        # JSTに変換（UTC+9時間）
        jst = datetime.timezone(datetime.timedelta(hours=9))
        now_jst = now.astimezone(jst)
        trial_end_jst = trial_end.astimezone(jst)

        # 戻り値用のデータ（JST）
        return {
            "current_sub_status": "try",
            "pending_action": None,
            "trial_start": now_jst.strftime('%Y年%m月%d日%H時%M分'),
            "trial_end": trial_end_jst.strftime('%Y年%m月%d日%H時%M分')
        }