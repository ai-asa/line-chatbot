import datetime
from firebase_admin import firestore

class FirestoreAdapter:

    def __init__(self):
        pass

    def update_history(self, db, userId, speaker, event_type, message):
        new_message = {
            "timestamp": datetime.datetime.now().isoformat(),
            "speaker": speaker,
            "event_type": event_type,
            "content": message
        }
        # user_idsコレクション内のユーザーIDドキュメントの参照を取得
        user_ids_ref = db.collection('user_ids').document(userId)

        # user_conversationsコレクション内のユーザーIDドキュメントの参照を取得
        user_conversations_ref = db.collection('user_conversations').document(userId)
        conversations_ref = user_conversations_ref.collection('conversations')

        # user_idsコレクションでユーザーIDの存在を確認
        if not user_ids_ref.get().exists:
            # user_idsコレクションにユーザーIDを追加
            user_ids_ref.set({'created_at': datetime.datetime.now().isoformat()})
            # user_conversationsコレクションにユーザーIDドキュメントとconversationsサブコレクションを作成
            user_conversations_ref.set({})
            conversations_ref.add(new_message)
        else:
            # ユーザーIDドキュメントが存在する場合、新しいメッセージを追加
            conversations_ref.add(new_message)

    def get_history(self, db, user_id,data_limit):
        # conversationsサブコレクションを参照
        conversations_ref = db.collection('user_conversations').document(user_id).collection('conversations')
        # 指定数の会話履歴スナップショットを取得
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(data_limit).get()
        # 会話履歴データの取得
        messages = [snapshot.to_dict() for snapshot in snapshots]
        return messages