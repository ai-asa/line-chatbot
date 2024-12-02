import requests

class LineAdapter:
    
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
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {accesstoken}'
        }
        messages = [
            {'type': 'text', 'text': text} for text in text_list
        ]
        data = {
            'to': to_user_id,
            'messages': messages
        }
        requests.post('https://api.line.me/v2/bot/message/push', headers=headers, json=data)