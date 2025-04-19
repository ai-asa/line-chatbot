import datetime
from firebase_admin import firestore
import numpy as np

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
            "pending_action": pending_action,
            "original_sub_status": current_status
        }
        if next_status:
            data["next_sub_status"] = next_status
        if plan_change_date:
            # タイムゾーン情報を含めて ISO フォーマットに変換
            data["plan_change_date"] = plan_change_date.isoformat()
        ref_userIds = db.collection('userIds').document(user_id)
        ref_userIds.set(data, merge=True)

    def set_new_sub(self, db, user_id, botType, new_status=None):
        """
        ・トライアルプランからの切り替え対応
        / 現在のプランを取得し、トライアルプランの場合はisTrialValidをFalseにする
        ・current_sub_status、botType、pending_actionを更新する
        """
        user_ref = db.collection('userIds').document(user_id)
        data = {
            "botType": botType,
            "isTrialValid": True
        }
        
        # new_statusが指定されている場合のみ更新
        if new_status is not None:
            data["current_sub_status"] = new_status
            data["original_sub_status"] = new_status
        
        # 現在トライアルプランの場合の処理
        doc = user_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            current_sub_status = user_data.get('current_sub_status')
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

    def update_history(self, db, userId, data_limit, user=None, assistant=None):
        """通常の会話履歴を更新する"""
        userIds_ref = db.collection('userIds').document(userId)
        conversations_ref = userIds_ref.collection('conversations')

        base_time = datetime.datetime.now(datetime.timezone.utc)
        
        if user:
            user_message = {
                "timestamp": base_time.isoformat(),
                "speaker": 'user',
                "content": user
            }
            conversations_ref.add(user_message)

        if assistant:
            assistant_message = {
                "timestamp": (base_time + datetime.timedelta(microseconds=1)).isoformat(),
                "speaker": 'assistant',
                "content": assistant
            }
            conversations_ref.add(assistant_message)

        # ユーザードキュメントが存在しない場合は初期化
        if not userIds_ref.get().exists:
            self.initialize_user_data(db, userId)

        # メッセージを timestamp の降順で取得
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).get()

        # メッセージの総数が指定数を超える場合、古いメッセージを削除
        if len(snapshots) > data_limit:
            # 10件目以降のメッセージを取得
            messages_to_delete = snapshots[data_limit:]
            # 古いメッセージを削除
            for snapshot in messages_to_delete:
                snapshot.reference.delete()

    def get_history(self, db, userId, data_limit):
        conversations_ref = db.collection('userIds').document(userId).collection('conversations')
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(data_limit).get()
        messages = [snapshot.to_dict() for snapshot in snapshots]
        return messages

    def _get_initial_fields(self):
        """
        ユーザーデータの初期フィールドを返します。
        """
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
            "original_sub_status": "free",
            'isAlreadyRP': False,
            'rp_setting': None,
            'rp_summary': None,
            'isRetryRP': False,
            'transfer_status': 0,
            'insurance_insured_info': None,
            'insurance_current_insurance': None,
            'insurance_target_insurance': None,
            'talk_status': 0,  # トークモードの状態を管理するフィールド
            'talk_personal_info': None,  # トークモードでの個人情報を保存するフィールド
            'talk_related_articles': None,  # トークモードでの関連記事を保存するフィールド
            'talk_mappings': None,  # トークモードでのマッピング情報を保存するフィールド
            'current_insurance_info': None, # 乗り換えモードでの現在の保険情報を保存するフィールド
            'target_insurance_info': None, # 乗り換えモードでの提案先の保険情報を保存するフィールド
            'proposal_text': None, # 乗り換えモードでの提案内容を保存するフィールド
            'talk_text': None, # トークモードでの提案内容を保存するフィールド
        }

    def get_user_data(self, db, user_id, data_limit, rp_data_limit):
        """
        指定した user_id に紐づくすべてのデータを取得します。
        サブステータスのチェックと更新（get_sub_status の処理）も含めています。
        必要なフィールドが欠けている場合は、初期値で補完します。
        """
        user_ref = db.collection('userIds').document(user_id)
        doc = user_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            update_data = {}  # 更新データを格納する辞書
            
            # 必要なフィールドの存在チェックと初期値設定
            initial_fields = self._get_initial_fields()
            
            # 欠けているフィールドを検出し、update_dataに追加
            for field, default_value in initial_fields.items():
                if field not in user_data and field not in ['conversations', 'rp_history']:
                    update_data[field] = default_value
                    user_data[field] = default_value
                    if field == 'original_sub_status':
                        update_data[field] = user_data.get('current_sub_status','free')
                        user_data[field] = user_data.get('current_sub_status','free')
            
            # トライアル期限チェック処理
            current_sub_status = user_data.get('current_sub_status','free')
            is_trial_valid = user_data.get('isTrialValid', True)
            trial_end_str = user_data.get('trial_end')
            next_sub_status = user_data.get('next_sub_status')
            plan_change_date_str = user_data.get('plan_change_date')
            now = datetime.datetime.now(datetime.timezone.utc)
            # 元のステータスに戻す
            original_sub_status = user_data.get('original_sub_status')
            if trial_end_str and  current_sub_status == 'try' and is_trial_valid:
                trial_end = datetime.datetime.fromisoformat(trial_end_str)
                if  now >= trial_end:
                    update_data.update({
                        'current_sub_status': original_sub_status,
                        'isTrialValid': False
                    })
                    user_data['current_sub_status'] = original_sub_status
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
            snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(data_limit).get()
            conversations = [snapshot.to_dict() for snapshot in snapshots]
            user_data['conversations'] = conversations
            
            # rp_history サブコレクションのデータ取得
            rp_history_ref = user_ref.collection('rp_history')
            rp_snapshots = rp_history_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(rp_data_limit).get()
            rp_history = [snapshot.to_dict() for snapshot in rp_snapshots]
            user_data['rp_history'] = rp_history

            # rp_full_history サブコレクションのデータ取得
            rp_full_history_ref = user_ref.collection('rp_full_history')
            rp_full_snapshots = rp_full_history_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).get()
            rp_full_history = [snapshot.to_dict() for snapshot in rp_full_snapshots]
            user_data['rp_full_history'] = rp_full_history
            
            return user_data
        else:
            # ユーザーデータが存在しない場合は初期化する
            self.initialize_user_data(db, user_id)
            return self._get_initial_fields()

    def initialize_user_data(self, db, user_id):
        """
        指定した user_id の完全なデータ構造を初期化します。
        既に存在するフィールドは上書きされません。
        """
        initial_data = self._get_initial_fields()
        user_ref = db.collection('userIds').document(user_id)
        # 既存のデータを上書きしないように merge=True を指定
        user_ref.set(initial_data, merge=True)

    def set_trial_period(self, db, user_id):
        """
        ユーザーのトライアル期間を設定します。
        trial_start に現在時刻を、trial_end に3日後の時刻を設定します。
        データベースにはUTCで保存し、戻り値はJST形式で返します。
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        trial_end = now + datetime.timedelta(days=3)

        # データベース保存用のデータ
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

    def reset_rp_history(self, db, user_id, isResetHistory=False, isResetFullHistory=False, isResetSummary=False, rp_setting=None, isAlreadyRP: bool = None, isRetryRP: bool = None):
        """RPの会話履歴とRP設定をリセットする
        
        ・必要なフィールド更新は単体のupdateで行い、
        サブコレクションの削除はバッチ書き込みで独立して実行する。
        ・トランザクションは、読み取りと書き込みの整合性が必要な場合に利用すべきで、
        単純な削除処理には不要です。
        """
        doc_ref = db.collection('userIds').document(user_id)
        update_data = {}
        
        if rp_setting is not None:
            update_data['rp_setting'] = rp_setting
        if isAlreadyRP is not None:
            update_data['isAlreadyRP'] = isAlreadyRP
        if isRetryRP is not None:
            update_data['isRetryRP'] = isRetryRP

        # まずドキュメントの更新（フィールドの更新はアトミックなので十分）
        if update_data:
            try:
                doc_ref.update(update_data)
            except Exception as e:
                print(f"Error updating user data: {e}")
                raise

        # サブコレクションのrp_historyの削除は、トランザクション内でなくバッチ処理で独立して実行
        if isResetHistory:
            try:
                batch = db.batch()
                rp_history_ref = doc_ref.collection('rp_history')
                docs = rp_history_ref.get()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
            except Exception as e:
                print(f"Error deleting rp_history subcollection: {e}")
                raise
        
        if isResetFullHistory:
            try:
                batch = db.batch()
                full_history_ref = doc_ref.collection('rp_full_history')
                docs = full_history_ref.get()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
            except Exception as e:
                print(f"Error deleting rp_full_history subcollection: {e}")
                raise

        if isResetSummary:
            try:
                doc_ref.update({
                    'rp_summary': None
                })
            except Exception as e:
                print(f"Error resetting rp_summary: {e}")
                raise
        

    def set_initial_rp(self, db, user_id, rp_setting):
        """初めてのRP設定を保存する"""
        doc_ref = db.collection('userIds').document(user_id)
        doc_ref.update({
            'isAlreadyRP': True,
            'rp_setting': rp_setting,
            'rp_summary': None,
            'rp_history': [],
            'rp_full_history': []
        })

    def update_rp_history(self, db, userId, rp_data_limit, salesperson=None, customer=None, summary=None):
        """RPの会話履歴を更新する"""
        userIds_ref = db.collection('userIds').document(userId)
        history_ref = userIds_ref.collection('rp_history')
        full_history_ref = userIds_ref.collection('rp_full_history')

        base_time = datetime.datetime.now(datetime.timezone.utc)
        
        # 通常の会話履歴の更新
        if salesperson:
            message = {
                "timestamp": base_time.isoformat(),
                "speaker": '保険営業員',
                "content": salesperson
            }
            history_ref.add(message)
            full_history_ref.add(message)  # 全文履歴にも追加

        if customer:
            message = {
                "timestamp": (base_time + datetime.timedelta(microseconds=1)).isoformat(),
                "speaker": 'ゼロコン',
                "content": customer
            }
            history_ref.add(message)
            full_history_ref.add(message)  # 全文履歴にも追加

        # 要約文の更新
        if summary is not None:
            userIds_ref.set({
                'rp_summary': summary
            }, merge=True)

        # ユーザードキュメントが存在しない場合は初期化
        if not userIds_ref.get().exists:
            self.initialize_user_data(db, userId)

        # メッセージを timestamp の降順で取得
        snapshots = history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).get()

        # メッセージの総数が指定数を超える場合、古いメッセージを削除
        if len(snapshots) > rp_data_limit:
            # 50件目以降のメッセージを取得
            messages_to_delete = snapshots[rp_data_limit:]
            # 古いメッセージを削除
            for snapshot in messages_to_delete:
                snapshot.reference.delete()

    def get_rp_history(self, db, userId, rp_data_limit):
        conversations_ref = db.collection('userIds').document(userId).collection('rp_history')
        snapshots = conversations_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(rp_data_limit).get()
        messages = [snapshot.to_dict() for snapshot in snapshots]
        return messages

    def update_insurance_state(self, db, user_id: str, transfer_status: int = None, info_type: str = None, info_data: dict = None, current_insurance_info: dict = None, target_insurance_info: dict = None, should_delete: bool = False, proposal_text: str = None):
        """保険関連の状態と情報を一括で更新する関数
        
        Args:
            db: Firestoreのデータベースインスタンス
            user_id (str): ユーザーID
            transfer_status (int, optional): 状態を示す数値
                0: 未選択/初期状態
                1: 被保険者の年齢、性別、その他の参考情報
                2: 現在の保険会社&保険商品名と値段を質問中
                3: 乗り換え先の保険商品名と値段を質問中
                4: 保険商品の情報を収集
                5: 乗り換え提案を作成
                6: 要約を提案している状態
                7: 提案が完了した状態
            info_type (str, optional): 情報の種類 ('insured_info' | 'current_insurance' | 'target_insurance')
            info_data (dict, optional): 保存するデータ
            current_insurance_info (dict, optional): 現在の保険情報
            target_insurance_info (dict, optional): 提案先の保険情報
            should_delete (bool, optional): 保険情報を削除するかどうか
        """
        doc_ref = db.collection('userIds').document(user_id)
        update_data = {}

        # transfer_statusの更新
        if transfer_status is not None:
            update_data.update({
                'transfer_status': transfer_status,
                'botType': 'tr'
            })

        # 保険情報の更新
        if info_type is not None and info_data is not None and not should_delete:
            update_data[f'insurance_{info_type}'] = info_data

        if current_insurance_info is not None:
            update_data['insurance_current_insurance'] = current_insurance_info

        if target_insurance_info is not None:
            update_data['insurance_target_insurance'] = target_insurance_info
        
        if proposal_text is not None:
            update_data['proposal_text'] = proposal_text

        # 保険情報の削除
        if should_delete:
            update_data.update({
                'insurance_insured_info': None,
                'insurance_current_insurance': None,
                'insurance_target_insurance': None,
                'current_insurance_info': None,
                'target_insurance_info': None,
                'proposal_text': None
            })

        # データの更新（一括で実行）
        if update_data:
            doc_ref.set(update_data, merge=True)
    
    
    def get_insurance_info(self, db, query_vector=None, limit=5):
        """保険情報をベクトル検索で取得する

        Args:
            db: Firestoreのデータベースインスタンス
            query_vector (list, optional): 検索クエリのベクトル表現。Defaults to None.
            limit (int, optional): 返す結果の最大件数。Defaults to 5.

        Returns:
            list: 保険情報のリスト。query_vectorが指定された場合は類似度順にソートされる。
            各要素は以下のキーを含む辞書:
            - company: 保険会社名
            - content: 保険の詳細内容
            - insurance_name: 保険商品名
            - summary: 保険の概要
            - similarity: クエリとの類似度（query_vectorが指定された場合のみ）
        """
        
        # insurancesコレクションの全batch_xドキュメントを取得
        batch_docs = db.collection('insurances').stream()
        
        if not batch_docs:
            return []
        
        all_insurance_info = []
        
        # 各batch_xドキュメントから保険情報を抽出
        for batch_doc in batch_docs:
            batch_data = batch_doc.to_dict()
            if 'insurance_list' not in batch_data:
                continue
                
            # insurance_listの各番号キーから保険情報を取得
            insurance_list = batch_data['insurance_list']
            if isinstance(insurance_list, dict):
                # 番号キーの値（保険情報）をリストに追加
                all_insurance_info.extend(insurance_list.values())
        
        # ベクトル検索が指定された場合
        if query_vector is not None:
            # クエリベクトルをNumPy配列に変換
            query_array = np.array(query_vector)
            
            # 各保険情報に対して類似度を計算
            results = []
            for info in all_insurance_info:
                if 'embedding' not in info:
                    continue
                    
                # 埋め込みベクトルをNumPy配列に変換
                embedding_array = np.array(info['embedding'])
                
                # ユークリッド距離を計算（L2ノルム）
                distance = np.linalg.norm(query_array - embedding_array)
                
                # 距離を0-1の類似度に変換（1が最も類似）
                similarity = 1 / (1 + distance)
                
                # 情報をコピーして類似度を追加
                info_with_similarity = info.copy()
                info_with_similarity['similarity'] = similarity
                results.append((similarity, info_with_similarity))
            
            # 類似度でソートして上位limit件を返す（類似度の降順）
            results.sort(key=lambda x: x[0], reverse=True)
            return [info for _, info in results[:limit]]
        
        # ベクトル検索が指定されていない場合は、単純にlimit件を返す
        return all_insurance_info[:limit]

    def update_talk_state(self, db, user_id: str, talk_status: int = None, personal_info: str = None, related_articles: list = None, talk_mappings: list = None, talk_text: str = None, should_delete: bool = False):
        """トークモードの状態と情報を一括で更新する関数
        
        Args:
            db: Firestoreのデータベースインスタンス
            user_id (str): ユーザーID
            talk_status (int, optional): 状態を示す数値
                0: 未選択/初期状態
                1: 個人情報を質問中/関連時事ネタの提供/続行確認
                2: マッピング作成/続行確認
                3: トーク生成中/続行確認
                4: 要約を提案している状態
                5: 提案が完了した状態
            personal_info (str, optional): 顧客個人情報
            related_articles (list, optional): 関連記事のリスト
            talk_mappings (list, optional): 保険提案トークのマッピングリスト
            should_delete (bool, optional): トーク情報を削除するかどうか
        """
        doc_ref = db.collection('userIds').document(user_id)
        update_data = {}

        # talk_statusの更新
        if talk_status is not None:
            update_data.update({
                'talk_status': talk_status,
                'botType': 'ta'
            })

        # 顧客個人情報の更新
        if personal_info is not None and not should_delete:
            update_data['talk_personal_info'] = personal_info

        # 関連記事情報の更新
        if related_articles is not None and not should_delete:
            update_data['talk_related_articles'] = related_articles

        # トークマッピングの更新
        if talk_mappings is not None and not should_delete:
            update_data['talk_mappings'] = talk_mappings

        # トークテキストの更新
        if talk_text is not None and not should_delete:
            update_data['talk_text'] = talk_text

        # トーク情報の削除
        if should_delete:
            update_data.update({
                'talk_personal_info': None,
                'talk_related_articles': None,
                'talk_mappings': None,
                'talk_text': None
            })

        # データの更新（一括で実行）
        if update_data:
            doc_ref.set(update_data, merge=True)

    def get_article_info(self, db, query_vector=None, limit=5):
        """記事情報をベクトル検索で取得する

        Args:
            db: Firestoreのデータベースインスタンス
            query_vector (list, optional): 検索クエリのベクトル表現。Defaults to None.
            limit (int, optional): 返す結果の最大件数。Defaults to 5.

        Returns:
            list: 記事情報のリスト。query_vectorが指定された場合は類似度順にソートされる。
            各要素は以下のキーを含む辞書:
            - title: 記事タイトル
            - content: 記事の内容
            - url: 記事のURL（存在する場合）
            - similarity: クエリとの類似度（query_vectorが指定された場合のみ）
        """
        
        # articlesコレクションのessential_infoドキュメントを取得
        doc_ref = db.collection('articles').document('essential_info')
        doc = doc_ref.get()
        
        if not doc.exists:
            return []
        
        doc_data = doc.to_dict()
        if 'info_list' not in doc_data:
            return []
            
        info_list = doc_data['info_list']
        all_article_info = []
        
        # info_listの各番号キーから記事情報を取得
        if isinstance(info_list, dict):
            # 番号キーの値（記事情報）をリストに追加
            all_article_info.extend(info_list.values())
        
        # ベクトル検索が指定された場合
        if query_vector is not None:
            # クエリベクトルをNumPy配列に変換
            query_array = np.array(query_vector)
            
            # 各記事情報に対して類似度を計算
            results = []
            for info in all_article_info:
                if 'embedding' not in info:
                    continue
                    
                # 埋め込みベクトルをNumPy配列に変換
                embedding_array = np.array(info['embedding'])
                
                # ユークリッド距離を計算（L2ノルム）
                distance = np.linalg.norm(query_array - embedding_array)
                
                # 距離を0-1の類似度に変換（1が最も類似）
                similarity = 1 / (1 + distance)
                
                # 情報をコピーして類似度を追加
                info_with_similarity = info.copy()
                info_with_similarity['similarity'] = similarity
                results.append((similarity, info_with_similarity))
            
            # 類似度でソートして上位limit件を返す（類似度の降順）
            results.sort(key=lambda x: x[0], reverse=True)
            return [info for _, info in results[:limit]]
        
        # ベクトル検索が指定されていない場合は、単純にlimit件を返す
        return all_article_info[:limit]

    def get_rp_prompt(self,rp_setting, history_text,user_input):
        if history_text == "":
            history_text = "まだ会話はありません\n"

        prompt = f"""あなたは以下の設定で説明される立場・人物像を持つ人物であり、現在、保険営業員からの保険提案を受けています。ガイドラインに従い、保険営業員の提案に応答してください。

あなたの設定：
<your_setting>
■ 名前：ゼロコン
{rp_setting}</your_setting>

ガイドライン：
1. 設定に準じた人物像を想定し、その性格や特性を考慮して会話を進めること
2. 設定に準じた人物の立場を想定し、抱える将来不安やニーズを想定して会話を進めること
3. 会話は営業員が主導できるように、なるべくあなたから質問してはならない
4. 営業員に保険を提案された際は、クリティカルな質問をすること
5. 最終的に、それまでの会話を考慮し、保険提案に対する成否を判断すること

現在の状況：
<situation>
訪問営業により、保険営業員があなたの家に来たところ
</situation>

これまでの会話：
<history>
{history_text}
</history>

現在の営業員の発言：
<current_comment>
{user_input}
</current_comment>

応答の注意事項：
- 適切に改行してください
- 自ら会話を振らず、あくまで営業員の発言に応答してください
- 返答は簡潔にし、質問があるとき以外は1文程度の短い文章で応答してください
- 要約文がある場合は、その内容を考慮して会話の一貫性を保ってください

営業員の発言に対し、応答してください："""
        return prompt