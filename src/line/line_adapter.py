import requests

class LineAdapter:
    # LINE Messaging APIの制限
    CHAR_LIMIT = 5000  # 1メッセージあたりの文字数制限
    MESSAGE_LIMIT = 5  # 1リクエストあたりのメッセージオブジェクト数制限
    
    def __init__(self):
        pass

    def reply_to_line(self, accesstoken, replyToken, text_list):
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {accesstoken}'
        }
        messages = [
            {'type': 'text', 'text': text} for text in text_list
        ]
        data = {
            'replyToken': replyToken,
            'messages': messages
        }
        requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)

    def push_message(self, accesstoken, to_user_id, text_list):
        """
        文字数制限とメッセージオブジェクト数制限を考慮してメッセージを分割して送信する
        
        Args:
            accesstoken (str): LINE APIトークン
            to_user_id (str): 送信先のユーザーID
            text_list (list): 送信するテキストのリスト
        """
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
                    requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)
                    
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
            requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)