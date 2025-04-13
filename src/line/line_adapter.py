import requests
import logging

class LineAdapter:
    # LINE Messaging APIの制限
    CHAR_LIMIT = 5000  # 1メッセージあたりの文字数制限
    MESSAGE_LIMIT = 5  # 1リクエストあたりのメッセージオブジェクト数制限
    
    def __init__(self):
        pass

    def reply_to_line(self, accesstoken, replyToken, text_list):
        logging.info(f"Replying to LINE with replyToken: {replyToken}, message count: {len(text_list)}")
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {accesstoken}'
        }
        
        # メッセージの長さをチェック
        if len(text_list) > self.MESSAGE_LIMIT:
            logging.warning(f"Message count exceeds LINE limit: {len(text_list)} > {self.MESSAGE_LIMIT}")
            # MESSAGE_LIMIT を超える場合は分割
            text_list = text_list[:self.MESSAGE_LIMIT]
            
        messages = [
            {'type': 'text', 'text': text} for text in text_list
        ]
        data = {
            'replyToken': replyToken,
            'messages': messages
        }
        logging.info(f"Sending LINE reply with data: {data}")
        
        # レスポンスを受け取る
        response = requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)
        
        if response.status_code != 200:
            logging.error(f"LINE API error: {response.status_code} - {response.text}")
        else:
            logging.info(f"LINE reply successful: {response.status_code}")
        
        return response

    def push_message(self, accesstoken, to_user_id, text_list):
        """
        文字数制限とメッセージオブジェクト数制限を考慮してメッセージを分割して送信する
        
        Args:
            accesstoken (str): LINE APIトークン
            to_user_id (str): 送信先のユーザーID
            text_list (list): 送信するテキストのリスト
        """
        logging.info(f"Pushing message to LINE user: {to_user_id}, message count: {len(text_list)}")
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {accesstoken}'
        }
        
        current_chunk = []
        current_length = 0
        current_count = 0
        
        for text in text_list:
            text_length = len(text)
            
            # 文字数制限またはメッセージ数制限を超える場合
            if (current_length + text_length > self.CHAR_LIMIT) or (current_count + 1 > self.MESSAGE_LIMIT):
                # 現在のチャンクが空でない場合は送信
                if current_chunk:
                    messages = [{'type': 'text', 'text': text} for text in current_chunk]
                    data = {
                        'to': to_user_id,
                        'messages': messages
                    }
                    logging.info(f"Sending LINE push chunk with {len(current_chunk)} messages")
                    response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
                    
                    if response.status_code != 200:
                        logging.error(f"LINE API push error: {response.status_code} - {response.text}")
                    
                # 新しいチャンクを開始
                current_chunk = [text]
                current_length = text_length
                current_count = 1
            else:
                # 現在のチャンクに追加
                current_chunk.append(text)
                current_length += text_length
                current_count += 1
        
        # 残りのチャンクを送信
        if current_chunk:
            messages = [{'type': 'text', 'text': text} for text in current_chunk]
            data = {
                'to': to_user_id,
                'messages': messages
            }
            logging.info(f"Sending final LINE push chunk with {len(current_chunk)} messages")
            response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
            
            if response.status_code != 200:
                logging.error(f"LINE API final push error: {response.status_code} - {response.text}")
            else:
                logging.info(f"LINE final push successful: {response.status_code}")