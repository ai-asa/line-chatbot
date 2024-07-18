import requests

class LineAdapter:
    
    def __init__(self):
        pass

    def reply_to_line(self, accesstoken, replyToken, text):
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': f'Bearer {accesstoken}'
        }
        data = {
            'replyToken': replyToken,
            'messages': [{'type': 'text', 'text': text}]
        }
        requests.post('https://api.line.me/v2/bot/message/reply', headers=headers, json=data)