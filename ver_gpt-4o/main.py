# %%
import os
import re
import functions_framework
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from dotenv import load_dotenv
import configparser
from src.firestore.firestore_adapter import FirestoreAdapter
from src.line.line_adapter import LineAdapter
from src.openai.openai_adapter import OpenaiAdapter
from src.openai.get_prompt import GetPrompt

# グローバル変数の定義
load_dotenv()
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
gp = GetPrompt()
la = LineAdapter()
fa = FirestoreAdapter()
oa = OpenaiAdapter()

# ※FirestoreのGoogle Cloud環境での認証と初期化
app = firebase_admin.initialize_app()
db = firestore.client()

# ※Firestoreのローカル環境での認証と初期化
#credentials_path = f"./secret-key/{os.getenv('CLOUD_FIRESTORE_JSON')}.json"
#cred = credentials.Certificate(credentials_path)
#app = firebase_admin.initialize_app(cred)
#db = firestore.client()

# 設定の読み込み(グローバル変数)
config = configparser.ConfigParser()
config.read('config.txt')
data_limit = int(config.get('CONFIG', 'data_limit', fallback=10))
token_limit = int(config.get('CONFIG', 'token_limit', fallback=2000))
retry_limit = int(config.get('CONFIG', 'retry_limit', fallback=5))
openai_model = config.get('CONFIG', 'openai_model', fallback='gpt-4-1106-preview')
openai_model_16k = config.get('INDEX', 'openai_model_16k', fallback='gpt-3.5-turbo-1106')
index_path = config.get('INDEX', 'index_path', fallback='./data/index/')
a_json_path = config.get('INDEX', 'a_json_path', fallback='./data/index/a_text.json')

def processQueryType(text):
    match = re.search(r'\d', text)
    if match:
        return int(match.group())
    else:
        return None

@functions_framework.http
def line_chatbot(request):
    request_json = request.get_json()
    for event in request_json["events"]:
        eventType = event['type']
        replyToken = event['replyToken']
        userId = event['source']['userId']
        # ユーザーID登録のハンドリング

        if eventType == "message":
            messageType = event['message']['type']
            if messageType == "text":
                userText = event['message']['text']
                class_prompt = gp.get_class_prompt(userText)
                query_type = processQueryType(oa.openai_chat("gpt-3.5-turbo-0125",class_prompt))
                if query_type == "3":
                    text = "個別商品についてはお答えできません、直接お問い合わせください"
                    la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, text)
                elif query_type == None:
                    text = "質問内容を取得できませんでした。もう一度送信してください。"
                    la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, text)
                else:
                    response_prompt = gp.get_response_prompt(query_type,userText)
                    response = oa.openai_chat("gpt-4o",response_prompt)
                    la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, response)
                # 会話履歴のハンドリング

            else:
                text = "テキストメッセージ以外にはご対応しておりません。"
                la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, text)
        elif eventType == "follow":
            pass
        elif eventType == "unfollow":
            pass
    return ('', 200) # ステータスコード200で空のレスポンスを返す


# %%
