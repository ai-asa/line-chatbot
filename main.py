# %%
import os
import re
import datetime
import requests
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
from src.rag.index_controller import IndexController
from src.youtube.youtube_data_api_adapter import YoutubeDataApiAdapter
from src.stripe.stripe_adapter import StripeAdapter
import random
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
INSURANCE_DB_URL = os.getenv('INSURANCE_DB_URL')
gp = GetPrompt()
la = LineAdapter()
fa = FirestoreAdapter()
oa = OpenaiAdapter()
ic = IndexController()
ya = YoutubeDataApiAdapter()
sa = StripeAdapter()

# ※FirestoreのGoogle Cloud環境での認証と初期化
app = firebase_admin.initialize_app()
db = firestore.client()

# ※Firestoreのローカル環境での認証と初期化
#credentials_path = f"./secret-key/{os.getenv('CLOUD_FIRESTORE_JSON')}.json"
#cred = credentials.Certificate(credentials_path)
#app = firebase_admin.initialize_app(cred)
#db = firestore.client()

config = configparser.ConfigParser()
config.read('config.ini')
data_limit = int(config.get('CONFIG', 'data_limit', fallback=10))
rp_data_limit = int(config.get('CONFIG', 'rp_data_limit', fallback=50))
token_limit = int(config.get('CONFIG', 'token_limit', fallback=2000))
retry_limit = int(config.get('CONFIG', 'retry_limit', fallback=5))
index_path = config.get('INDEX', 'index_path', fallback='./data/index/')
a_json_path = config.get('INDEX', 'a_json_path', fallback='./data/index/a_text.json')

PLAN_NAMES = {
    '980': 'ゼロコン初級プラン',
    '1980': 'ゼロコン中級プラン',
    '3980': 'ゼロコン上級プラン',
    'free': 'フリープラン',
    'try': 'トライアルプラン'
}
# PRICE_IDS = {
#     'price_1QDau2GUmbNfqrzFFvHVvoaz': '980',
#     'price_1QDaxQGUmbNfqrzFniNnEiyF': '1980',
#     'price_1RFb85GUmbNfqrzFReo445kQ': '3980'
# }
# テスト用
PRICE_IDS = {
    'price_1QNPhlRo65d8y4fN7jsiQwmf': '980',
    'price_1QNPhyRo65d8y4fNmYAj1ZSP': '1980',
    'price_1QNPiCRo65d8y4fNwGGoKq6y': '3980'
}
PLAN_ORDER = ['free', '980', '1980', '3980']

# RPの設定用の定数
RP_AGES = [
    "25歳", "30歳", "35歳", "40歳", "45歳", "50歳", "55歳", "60歳"
]

RP_GENDERS = ["男性", "女性"]

RP_ANNUAL_INCOMES = [
    "300万円", "400万円", "500万円", "600万円", "700万円", 
    "800万円", "1000万円", "1200万円", "1500万円"
]

RP_FAMILY_STRUCTURES = [
    "独身", "既婚・子供なし", "既婚・子供1人", "既婚・子供2人",
    "既婚・子供3人", "シングルペアレント・子供1人", "シングルペアレント・子供2人"
]

RP_LOCATIONS = [
    "都内", "大都市圏", "地方"
]

RP_RESIDENCES = [
    "一戸建て", "マンション", "賃貸アパート"
]

RP_INSURANCE_STATUS = [
    "保険未加入", 
    "生命保険のみ加入", 
    "医療保険のみ加入",
    "生命保険・医療保険に加入",
    "生命保険・医療保険・がん保険に加入"
]

RP_INSURANCE_DETAILS = [
    "月額 5,000円", 
    "月額 10,000円",
    "月額 15,000円",
    "月額 20,000円",
    "月額 30,000円"
]

RP_PERSONALITIES = [
    "慎重派で保守的", "気難しく否定的",
    "受容的で共感力が高い", "論理的で理屈屋"
]

# 保険会社のリストを追加
RP_LIFE_INSURANCE_COMPANIES = [
    "日本生命", "第一生命", "明治安田", "住友",
    "T&D", "ソニー", "朝日"
]
RP_MEDICAL_INSURANCE_COMPANIES = [
    "楽天", "アフラック", "チューリッヒ", "アクサ",
    "メットライフ", "東京海上日動", "三井住友海上", "明治安田"
]
RP_CANCER_INSURANCE_COMPANIES = [
    "アクサ", "第一生命", "明治安田", "住友", "メットライフ",
    "アフラック", "チューリッヒ", "日本生命", "三井住友海上", "朝日"
]

def generate_rp_setting():
    """RPの設定をランダムに生成する"""
    setting = {
        "年齢": random.choice(RP_AGES),
        "性別": random.choice(RP_GENDERS),
        "世帯年収": random.choice(RP_ANNUAL_INCOMES),
        "家族構成": random.choice(RP_FAMILY_STRUCTURES),
        "居住地": random.choice(RP_LOCATIONS),
        "住居形態": random.choice(RP_RESIDENCES),
        "保険加入状況": random.choice(RP_INSURANCE_STATUS),
        "現在の保険料": random.choice(RP_INSURANCE_DETAILS),
        "性格": random.choice(RP_PERSONALITIES)
    }
    
    # 保険加入状況に応じて保険会社の情報を追加
    if setting["保険加入状況"] != "保険未加入":
        if "生命保険" in setting["保険加入状況"]:
            setting["生命保険会社"] = random.choice(RP_LIFE_INSURANCE_COMPANIES)
        if "医療保険" in setting["保険加入状況"]:
            setting["医療保険会社"] = random.choice(RP_MEDICAL_INSURANCE_COMPANIES)
        if "がん保険" in setting["保険加入状況"]:
            setting["がん保険会社"] = random.choice(RP_CANCER_INSURANCE_COMPANIES)
    
    # 設定を文字列にフォーマット
    setting_text = ""
    for key, value in setting.items():
        setting_text += f"■ {key}：{value}\n"
    
    return setting_text

@functions_framework.http
def line_chatbot(request):
    request_json = request.get_json()
    event_type = request_json.get('type')
    if event_type:
        results = stripe_event_process(request_json,event_type)
    else:
        results = line_event_process(request_json)
    if all(results):
        return ('', 200)
    else:
        return ('', 500)

def stripe_event_process(request_json,event_type):
    results = []
    if event_type == 'customer.subscription.created':
        result = reg_sub(request_json)
    elif event_type == 'customer.subscription.updated':
        result = update_sub(request_json)
    elif event_type == 'customer.subscription.deleted':
        result = del_sub(request_json)
    else:
        result = False
    results.append(result)
    return results

def reg_sub(request_json):
    # try:
    sub_id = request_json['data']['object']['id']
    product_info, userId = sa.fetch_checkout_data(sub_id)
    new_plan = PRICE_IDS.get(product_info['price_id'], 'unknown_plan')
    fa.set_new_sub(db, userId, 'fr', new_status=new_plan)
    text = reg_sub_text(new_plan)
    la.push_message(LINE_ACCESS_TOKEN, userId, text)
    return True
    # except Exception as e:
    #     print(e)
    #     return False

def reg_sub_text(new_plan):
    return [f'【ご契約通知】\n「{PLAN_NAMES[new_plan]}」へのご契約が完了しました。\n\nご利用いただき誠にありがとうございます']

def update_sub(request_json):
    # try:
    sub = request_json['data']['object']
    sub_id = sub['id']
    _, userId = sa.fetch_checkout_data(sub_id)
    pre_ats = request_json['data'].get('previous_attributes', {})
    cancel_priod = sub.get('cancel_at_period_end',False)
    text = ""
    # 解約予約の場合
    if 'cancel_at_period_end' in pre_ats and cancel_priod:
        text = res_cancel(sub,userId)
    # グレード変更の場合
    elif 'items' in pre_ats:
        text = ud_grade(sub,userId,pre_ats)
    la.push_message(LINE_ACCESS_TOKEN, userId, text)
    return True
    # except Exception as e:
    #     print(e)
    #     return False
    
def res_cancel(sub,userId):
    plan_period = datetime.datetime.fromtimestamp(sub['current_period_end'], datetime.timezone.utc)
    # firestoreから現在のステータスを取得
    # cu_sta_data = fa.get_sub_status(db, userId)
    user_data = fa.get_user_data(db,userId,data_limit,rp_data_limit)
    cu_sta = user_data['current_sub_status']
    # Firestoreの状態を更新（next_sub_status と plan_change_date を設定）
    fa.set_sub_status(db,userId,current_status=cu_sta,next_status='free',plan_change_date=plan_period)

    return [f'【解約予約通知】\nご契約プランの解約予約が完了しました\n\n現在のプランは{plan_period.strftime("%Y年%m月%d日 %H:%M:%S")}までご利用可能です']

def ud_grade(sub,userId,pre_ats):
    old_price_id = pre_ats['items']['data'][0]['price']['id']
    old_plan = PRICE_IDS.get(old_price_id, 'unknown_plan')
    old_plan_index = PLAN_ORDER.index(old_plan) if old_plan in PLAN_ORDER else -1
    new_price_id = sub['items']['data'][0]['price']['id']
    new_plan = PRICE_IDS.get(new_price_id, 'unknown_plan')
    new_plan_index = PLAN_ORDER.index(new_plan) if new_plan in PLAN_ORDER else -1
    # アップグレードの場合
    if new_plan_index > old_plan_index:
        return upgrade_fs_sub(userId,new_plan)
    # ダウングレードの場合
    elif new_plan_index < old_plan_index:
        return downgrade_fs_sub(sub,userId,old_plan,new_plan)

def upgrade_fs_sub(userId,new_plan):
    fa.set_botType(db, userId, 'fr')
    fa.set_sub_status(db,userId,current_status=new_plan)
    return [f'【プラン変更通知】\n「{PLAN_NAMES[new_plan]}」への変更が完了しました。\n\nご利用いただき誠にありがとうございます']

def downgrade_fs_sub(sub,userId,old_plan,new_plan):
    plan_change_date = datetime.datetime.fromtimestamp(sub['current_period_end'], datetime.timezone.utc)
    fa.set_botType(db, userId, 'fr')
    fa.set_sub_status(db,userId,current_status=old_plan,next_status=new_plan,plan_change_date=plan_change_date)
    return [f'【プラン変更通知】\n「{PLAN_NAMES[new_plan]}」への変更が予約されました。\n\n現在のプランは{plan_change_date.strftime("%Y年%m月%d日 %H:%M:%S")}までご利用いただけます']

def del_sub(request_json):
    # try:
    sub_id = request_json['data']['object']['id']
    _, userId = sa.fetch_checkout_data(sub_id)
    fa.set_botType(db, userId, 'fr')
    fa.set_sub_status(db,userId,current_status='free',next_status=None,plan_change_date=None)
    text = del_sub_text()
    la.push_message(LINE_ACCESS_TOKEN, userId, text)
    return True
    # except Exception as e:
    #     print(e)
    #     return False

def del_sub_text():
    return ['【解約通知】\nご契約プランの解約が完了しました\n\nご利用いただき誠にありがとうございました','現在のプランはフリープランです']

def line_event_process(request_json):
    results = []
    for event in request_json["events"]:
        eventType = event['type']
        userId = event['source']['userId']
        try:
            replyToken = event['replyToken']
        except Exception as e:
            replyToken = None
            print(e)

        user_data = fa.get_user_data(db,userId,data_limit,rp_data_limit)
        if eventType == "message":
            result = event_message(event,replyToken,userId,user_data)
        elif eventType == "follow":
            result = event_follow(event,replyToken,userId)
        elif eventType == "unfollow":
            result = event_unfollow(event,replyToken,userId)
        elif eventType == "postback":
            result = event_postback(event,replyToken,userId,user_data)
        results.append(result) 
    return results

def event_message(event,replyToken,userId,user_data):
    # try:
    res = []
    mesType = event['message']['type']
    if mesType == "text":
        res = message_process(event,userId,user_data)
    else:
        res = ["テキストメッセージ以外には対応していません"]
    try:
        # 空のリストは送信しない（すでに別の方法で送信済み）
        if res and len(res) > 0:
            logging.info(f"Replying to message event with {len(res)} messages")
            la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, res)
        else:
            logging.info("Skipping reply as response list is empty")
    except Exception as e:
        logging.error(f"Error in event_message: {str(e)}")
        # 返信に失敗した場合はプッシュメッセージを試みる
        if res and len(res) > 0:
            la.push_message(LINE_ACCESS_TOKEN, userId, res)
    return True
    # except Exception as e:
    #     print(e)
    #     return False
    
def message_process(event,userId,user_data):
    mesText = event['message']['text']
    pending_action = user_data['pending_action']
    isRetryRP = user_data['isRetryRP']

    if pending_action: # サブスクリプションのアクションが保留されている場合
        return sub_act(pending_action,mesText,userId,user_data)
    elif isRetryRP: # RPをリトライ要請されている場合
        return retry_rp(userId,mesText,user_data)
    else:
        mt = messageText(event,userId,mesText,user_data)
        return mt.res_text()

def sub_act(pending_action,mesText,userId,user_data):
    if mesText == 'はい':
        return exec_update_sub(pending_action,userId,user_data)
    else:
        return cancel_update_sub(userId)

def retry_rp(userId,mesText,user_data):
    situation = rp_situation(user_data)    
    if mesText == 'はい':
        fa.reset_rp_history(db, userId, isResetHistory=True, isResetFullHistory=True, isResetSummary=True, isRetryRP=False)
        return ["会話履歴をリセットし、同じ設定で再度営業ロープレを開始します", f"====シチュエーション====\n{situation}※設定は他にも存在します！会話の中で引き出してください\n\n=====================\n\nテキストを送信し、会話を開始してください..."]
    else:
        return close_rp(userId)

def rp_situation(user_data, rp_setting=None):
    """RPの設定から場面の説明を生成する"""
    if rp_setting is None:
        rp_setting_text = user_data.get('rp_setting')
    else:
        rp_setting_text = rp_setting
    
    # 文字列から必要な情報を抽出
    setting_dict = {}
    for line in rp_setting_text.split('\n'):
        if '：' in line:
            key, value = line.split('：')
            key = key.replace('■ ', '').strip()
            value = value.strip()
            setting_dict[key] = value

    situation = "■ 場面：訪問営業\n"
    situation += f"■ 場所：{setting_dict.get('居住地', '不明')} / {setting_dict.get('住居形態', '不明')}\n"
    situation += f"■ 顧客：{setting_dict.get('性別', '不明')} / {setting_dict.get('年齢', '不明')}くらい\n"
    return situation

def close_rp(userId):
    fa.reset_rp_history(db, userId, isResetHistory=True, isResetFullHistory=True, isResetSummary=True, isAlreadyRP=False, isRetryRP=False)
    return ["営業ロープレを終了します。\n\nお疲れさまでした！", "繰り返し練習し、営業力を高めましょう！"]

def exec_update_sub(pending_action,userId,user_data):
    if pending_action['desired_plan'] == 'try':
        return exec_start_trial(userId)
    cus_id = sa.get_customer_id(userId)
    cu_sub = sa.get_current_subscription(cus_id)
    sub_id = cu_sub.id
    new_price_id = sa.PRICE_IDS[pending_action['desired_plan']]
    if pending_action['action'] == 'upgrade':
        return exec_upgrade_sub(sub_id,new_price_id,userId,pending_action)
    elif pending_action['action'] == 'downgrade':
        return exec_downgrade_sub(sub_id,new_price_id,userId,pending_action,user_data)
    else:
        return ['不明なアクションです。']
    
def exec_start_trial(userId):
    trial_data = fa.set_trial_period(db,userId)
    trial_start = trial_data['trial_start']
    trial_end = trial_data['trial_end']
    return ["【開始通知】\n無料トライアルが開始されました", f"期間は{trial_start}から{trial_end}までです","期間中は上級プランと同様の機能をご利用いただけます", "ご利用いただき誠にありがとうございます"]

def exec_upgrade_sub(sub_id,new_price_id,userId,pending_action):
    sa.upgrade_subscription(sub_id, new_price_id)
    fa.set_sub_status(db, userId, current_status=pending_action['desired_plan'])
    return ['更新処理中']

def exec_downgrade_sub(sub_id,new_price_id,userId,pending_action,user_data):
    sa.downgrade_subscription(sub_id, new_price_id)
    plan_change_date = sa.get_plan_change_date(sub_id)
    # sub_status = fa.get_sub_status(db, userId)
    fa.set_sub_status(db,userId,current_status=user_data['current_sub_status'],next_status=pending_action['desired_plan'],plan_change_date=plan_change_date)
    return ['更新処理中']

def cancel_update_sub(userId):
    fa.clear_pending_action(db, userId)
    return ['操作をキャンセルしました']

def event_follow(event,replyToken,userId):
    # user_data = fa.get_user_data(db,userId,data_limit,rp_data_limit)
    return True
    # except Exception as e:
    #     print(e)
    #     return False
    
def event_unfollow(event,replyToken,userId):
    return True

def event_postback(event,replyToken,userId,user_data):
    pending_action = user_data['pending_action']
    isRetryRP = user_data['isRetryRP']
    transfer_status = user_data.get('transfer_status', 0)
    talk_status = user_data.get('talk_status', 0)
    if 1 <= transfer_status <= 7:
        fa.update_insurance_state(db, userId, transfer_status=0, should_delete=True)
    elif 1 <= talk_status <= 5:
        fa.update_talk_state(db, userId, talk_status=0, should_delete=True)
    elif pending_action:
        text = cancel_update_sub(userId)
    elif isRetryRP:
        text = close_rp(userId)
        la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, text)
        return True
    postType = event['postback']['data']
    if postType in ['kn','gs','ta','tr','rps','rpr']:
        res = mode_change(userId,postType,user_data)
    elif postType in ['980','1980','3980','free','try']:
        rs = RegStripe(event,postType,replyToken,userId,user_data)
        res = rs.stripe_post_process()
    elif postType == 'tab':
        return True
    else:
        res = ["現在開発中のメニューです。今後の更新にご期待ください"]
    # try:
    la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, res)
    return True
    # except Exception as e:
    #     print(e)
    #     return False

def mode_change(userId,postType,user_data):
    current_plan = user_data['current_sub_status']
    if postType == "kn":
        judg,text = mode_kn(current_plan)
    # elif postType == "qa":
    #     judg,text = mode_qa(current_plan)
    # elif postType == "yo":
    #     judg,text = mode_yo(current_plan)
    elif postType == "ta":
        judg,text = mode_ta(userId,current_plan)
    elif postType == "tr":
        judg,text = mode_tr(userId,current_plan)
    elif postType == "gs":
        judg,text = mode_gs(current_plan)
    elif postType == "rps":
        judg,text = mode_rps(userId,current_plan,user_data)
    elif postType == "rpr":
        judg,text = mode_rpr(userId,current_plan,user_data)
    if judg:
        fa.set_botType(db, userId, postType)
    return text

def mode_kn(current_plan):
    if current_plan == 'free':
        return False, ["本機能は各種プランへご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが保険の知識・提案方法に関して一問一答でお答えします"]

# def mode_qa(current_plan):
#     if current_plan in ['free','980']:
#         return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
#     else:
#         return True, ["【モード変更】\nゼロコンAIが保険に関するQAデータベースに基づいてお答えします"]
    
# def mode_yo(current_plan):
#     if current_plan in ['free','980']:
#         return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
#     else:
#         return True, ["【モード変更】\nゼロコンAIが知りたい情報についてYoutube動画をお調べします"]

def mode_gs(current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが会話形式で様々な質問、ご相談に対応します"]

def mode_ta(userId,current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, ta_text(userId)
    
def mode_tr(userId,current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, tr_text(userId)

def mode_rps(userId,current_plan,user_data):
    if current_plan in ['free','980','1980']:
        return False, ["本機能は上級プランにご契約いただくことでご利用いただけます"]
    else:
        return True, rps_text(userId,user_data)
    
def mode_rpr(userId,current_plan,user_data):
    if current_plan in ['free','980', '1980']:
        return False, ["本機能は上級プランにご契約いただくことでご利用いただけます"]
    else:
        return True, rpr_text(userId,user_data)

def ta_text(userId):
    """
    トークモードの状態を設定し、個人情報を質問するリプライを返す
    """
    # トークモードの状態を1（個人情報を質問中）に設定
    fa.update_talk_state(db, userId, talk_status=1)
    
    return ["【モード変更】\nゼロコンAIが保険提案トークを考えます",
            "はじめに、想定するお客様の情報を教えてください♩\n\n--------------","年齢:30代\n性別:女性\n家族構成:夫婦2人\n職業:会社員\n居住地:東京都",
            "--------------\n\n点線内だけをコピペして、内容を変えて送信してね(^^♪",
            "※項目は増やしてもOKです。情報が多いほど、より良い提案ができるよ！"]

def tr_text(userId):
    """
    保険商品の乗り換え提案機能の状態を設定し、
    被保険者の現在加入している保険商品名とその保険会社名を質問するリプライを返す
    """
    # 乗り換え提案の状態を1（被保険者の年齢と性別を質問中）に設定
    fa.update_insurance_state(db, userId, transfer_status=1)
    
    return ["【モード変更】\nゼロコンAIが保険商品の乗り換えを提案します",
            "はじめに、想定するお客様の情報を教えてください♩\n\n--------------","年齢:45歳\n性別:男性\n職業:会社員\n保険の目的:死亡保障と子供の積立、老後の資産\n死亡受取:配偶者",
            "--------------\n\n点線内だけをコピペして、内容を変えて送信してね(^^♪",
            "※項目は増やしてもOKです。情報が多いほど、より良い提案ができるよ！"]

def rps_text(userId,user_data):
    """RPの設定を生成し、テキストを返す"""
    # RP設定を生成
    rp_setting = generate_rp_setting()
    situation = rp_situation(user_data, rp_setting)
    if user_data['isAlreadyRP']:
        # 会話履歴とRP設定更新
        fa.reset_rp_history(db, userId, isResetHistory=True, isResetFullHistory=True, isResetSummary=True, rp_setting=rp_setting)
        return ["これまでの営業ロープレの会話履歴と設定をリセットしました。\n\n新たに営業ロープレを開始します",f"====シチュエーション====\n{situation}※設定は他にも存在します！会話でお客様の状況を引き出してください=====================\n\nテキストを送信し、会話を開始してください..."]
    else:
        fa.set_initial_rp(db, userId, rp_setting)
        return ["【モード変更】\nゼロコンAIを相手に営業トレーニング！\n※本機能はプロトタイプ版です", "ゼロコンAIがランダムな設定のお客様を演じます。ゼロコンAIに対し、保険営業を行ってください！\n※顧客の設定はランダムに決められます", "メニューの「終了＆批評」ボタンをクリックすると営業ロープレを終了し、営業提案の内容を評価します",  "では、営業ロープレを開始します",f"====シチュエーション====\n{situation}※設定は他にも存在します！会話の中で探してください=====================\n\nテキストを送信し、会話を開始してください..."]

def rpr_text(userId,user_data):
    """
    営業ロープレの会話履歴を取得し、それを基にAIにて批評を行い、テキストを返す
    """
    if not user_data['isAlreadyRP']:
        return ["営業ロープレは開始されていません", "営業ロープレを開始するには、メニューの「開始＆リセット」ボタンをクリックしてください"]
    rp_full_history = user_data['rp_full_history']
    rp_full_history_text = get_text(rp_full_history)
    rp_setting = user_data['rp_setting']

    res = oa.openai_chat("gpt-4.1",gp.get_rpr_prompt(rp_setting,rp_full_history_text))
    response = re.search(r'<output_format>(.*?)</output_format>', res, re.DOTALL)
    if not response:
        return ["評価の取得に失敗しました。再度、メニューから「終了＆フィードバック」を選択してください"]
    
    text = []
    if res == None:
        text = ["営業ロープレを終了し、ゼロコンAIによる提案の評価を行います！","申し訳ございません。エラーにより、評価結果が取得できませんでした"]
    else:
        text = ["営業ロープレを終了し、ゼロコンAIによる提案の評価を行います！", 
                "まず、今回の私(お客様)の設定は以下の通りでした。\n\n【お客様の設定】\n" + rp_setting, 
                "提案の評価は以下の通りです。\n\n======提案の評価======\n" + response.group(1) +"\n=====================\n※本機能はプロトタイプ版です"]
    
    restart_text = ["もう一度同じ設定で営業ロープレを開始しますか？", 
                    "※「はい」と返信すると会話をリセットし、同じ設定で営業ロープレを開始します\n(モード切替や「はい」以外の返信で終了します)"]
    
    text.extend(restart_text)
    fa.reset_rp_history(db, userId, isResetHistory=True, isResetFullHistory=True, isResetSummary=True, isRetryRP=True)
    return text

def get_text(rp_history):
    text_list = []
    for conv in rp_history:
        text = f"""
<speaker>{conv['speaker']}</speaker>
<message>{conv['content']}</message>"""
        text_list.append(text)
    return "".join(text_list)

# def norm_rpr_text(text):
#     pattern = r'<response>(.*?)</response>'
#     match = re.search(pattern, text, re.DOTALL)
#     if match:
#         return match.group(1).strip()
#     return None

class RegStripe:
    def __init__(self,event,postType,replyToken,userId,user_data):
        self.event = event
        self.postType = postType
        self.replyToken = replyToken
        self.userId = userId
        self.user_data = user_data
    
    def stripe_post_process(self):
        current_plan = self.user_data['current_sub_status']
        original_plan = self.user_data['original_sub_status']
        next_plan = self.user_data['next_sub_status']
        isTrialValid = self.user_data['isTrialValid']
        action = self.det_sub_act(current_plan, original_plan, next_plan, self.postType)
        if action == 'free':
            return self.cancel_sub(current_plan,next_plan)
        elif action == 'start_trial':
            return self.start_trial(action,self.postType,isTrialValid)
        elif action == 'invalid_trial':
            return ['有料プランから無料トライアルへの変更はできません']
        elif action == 'new_subscription':
            return self.new_sub(self.postType)
        elif action == 'upgrade':
            return self.upgrade_sub(action,next_plan,self.postType)
        elif action == 'downgrade':
            return self.downgrade_sub(action,next_plan,self.postType)
        elif action == 'already_resv':
            return ['既に選択されたプランへの変更を予約済みです']
        elif action == 'downgrade_resv':
            return [f'「{PLAN_NAMES[next_plan]}」への変更が予約済みのため、現在プラン変更をお受けできません']
        elif action == 'already_subscribed':
            return ['既に選択されたプランにご契約済みです']
        else:
            return ['不正な操作です']

    def det_sub_act(self, current_plan, original_plan, next_plan, desired_plan):
        plan_order = ['free', 'try', '980', '1980', '3980']
        original_index = plan_order.index(original_plan)
        current_index = plan_order.index(current_plan)
        if next_plan is None:
            next_index = 6
        else:
            next_index = plan_order.index(next_plan)
        desired_index = plan_order.index(desired_plan)

        if desired_plan == 'free':
            return 'free'
        elif (current_plan == 'free' or current_plan == '980') and desired_plan == 'try': # フリー・初級からトライアルへは移行可能
            return 'start_trial'
        elif desired_plan == 'try' and original_index > 3: # 中上級プランからトライアルへ移行不可
            return 'invalid_trial'
        elif desired_index == original_index or current_index == desired_index: # 同じプランに変更不可
            return 'already_subscribed'
        elif desired_plan == next_plan: # 予約済みプランに変更不可
            return 'already_resv'
        elif next_plan != 'free' and original_index > next_index: # ダウングレード予約済み
            return 'downgrade_resv'
        elif (original_plan == 'free' or original_plan == 'try') and desired_plan in ['980', '1980', '3980']: # 新規登録
            return 'new_subscription'
        elif original_index < desired_index: # アップグレード
            return 'upgrade'
        elif original_index > desired_index: # ダウングレード
            return 'downgrade'
        else:
            return 'already_subscribed'
    
    def start_trial(self,action,desired_plan,isTrialValid):
        if isTrialValid:
            fa.set_pending_action(db, self.userId, {'action': action, 'desired_plan': desired_plan})
            return ["【ご確認】\n3日間の無料トライアルを開始しますか？","※※※※※※※※※※※※※※※※※※※※※※\n\n・無料トライアル期間は3日間です\n\n・トライアル中は、上級プランと同様の機能がお使いいただけます\n\n・トライアル終了後は、もとのプランに戻ります\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください\n(モード切替や「はい」以外の返信でキャンセルします)"]
        else:
            return ['トライアル期間が終了しています']

    def cancel_sub(self,current_plan,next_plan):
        if current_plan == 'free':
            return ['ご契約済みのプランはありません']
        elif current_plan == 'try':
            return ['現在トライアルご契約中であり、ご契約済みの有料プランはありません']
        elif next_plan == 'free':
            return ['ご契約プランの解約予約は完了しています']
        else:
            return ['【解約予約用URL】\nご契約プランの解約をご希望の場合は以下のURLから手続きください', sa.create_cancel_session(self.userId), '※※※※※※※※※※※※※※※※※※※※※※\n解約につき以下の点にご注意ください\n\n・解約は当契約月の最終日に完了します\n\n・解約完了までは引き続き現在のプランをご利用可能です\n\n・プラン変更はできなくなります。解約完了後に再度ご契約ください\n\n※※※※※※※※※※※※※※※※※※※※※※']

    def new_sub(self,desired_plan):
        return ["【ご契約用URL】\n以下のURLからご契約手続きを進めてください\n\n" + sa.create_checkout_session(self.userId, desired_plan),'無料トライアルをご利用の場合はご契約が完了次第、解除されます']

    def upgrade_sub(self,action,next_plan,desired_plan):
        if next_plan == 'free':
            return ['【ご連絡】\n解約予約されているため、プランの変更はできません\n\n解約完了後に再度ご契約ください']
        else:
            fa.set_pending_action(db, self.userId, {'action': action, 'desired_plan': desired_plan})
            return [f"【ご契約内容の変更確認】\nご契約のプランを「{PLAN_NAMES[desired_plan]}」に変更します","※※※※※※※※※※※※※※※※※※※※※※\n\n・「はい」と返信いただくと、即時契約手続きが実行されます\n\n・本契約月から料金が発生します\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください\n(モード切替や「はい」以外の返信でキャンセルします)"]

    def downgrade_sub(self,action,next_plan,desired_plan):
        if next_plan == 'free':
            return ['【ご連絡】\n解約予約されているため、プランの変更はできません\n\n解約完了後に再度ご契約ください']
        else:
            fa.set_pending_action(db, self.userId, {'action': action, 'desired_plan': desired_plan})
            return [f"【ご契約内容の変更予約の確認】\nご契約のプランを「{PLAN_NAMES[desired_plan]}」に変更予約します","※※※※※※※※※※※※※※※※※※※※※※\nプラン変更予約につき以下の点にご注意ください\n\n・本契約月は現在プランの料金が適用され、翌契約月から予約プランの料金が適用されます\n\n・プラン変更の完了まで、引き続き現在プランの機能をご利用可能です\n\n・プラン変更が完了するまで、他プランへの変更はできません\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください\n(モード切替や「はい」以外の返信でキャンセルします)"]

class messageText:
    def __init__(self,event,userId,userText,user_data):
        self.userText = userText
        self.userId = userId
        self.userData = user_data
    
    def res_text(self):
        currentPlan = self.userData['current_sub_status']
        botType = self.userData['botType']
        if currentPlan == 'free':
            return ['チャット機能をご利用いただくには、無料トライアルか有料プランへのご契約が必要です', 'メニューから「プランの変更・契約」をタップしてご確認ください']
        if currentPlan == '980':
            return self.processBegin(botType)
        elif currentPlan == '1980':
            return self.processMiddle(botType)
        elif currentPlan == 'try' or currentPlan == '3980':
            return self.processHigh(botType)
    
    def processBegin(self,botType):
        if botType == "fr":
            return ['メニューからモードを選択してください']
        elif botType == "kn":
            return self.res_kn()
        elif botType == "gs":
            return self.res_gs()
        elif botType == "tr" or botType == "ta":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        elif botType == "rps" or botType == "rpr":
            return ['本機能をご利用いただくには、上級プランにご契約いただく必要があります']
        else:
            return ['エラー：無効なモードを指定しています。別のモードを選択してください']
    
    def processMiddle(self,botType):
        if botType == "fr":
            return ['メニューからモードを選択してください']
        elif botType == "kn":
            return self.res_kn()
        elif botType == "gs":
            return self.res_gs()
        elif botType == "tr":
            return self.res_tr()
        elif botType == "ta":
            return self.res_ta()
        elif botType == "rps" or botType == "rpr":
            return ['本機能をご利用いただくには、上級プランにご契約いただく必要があります']
        else:
            return ['エラー：無効なモードを指定しています。別のモードを選択してください']

    def processHigh(self,botType):
        if botType == "fr":
            return ['メニューからモードを選択してください']
        elif botType == "kn":
            return self.res_kn()
        elif botType == "gs":
            return self.res_gs()
        elif botType == "tr":
            return self.res_tr()
        elif botType == "ta":
            return self.res_ta()
        elif botType == "rps" or botType == "rpr":
            return self.res_rp()
        else:
            return ['エラー：無効なモードを指定しています。別のモードを選択してください']

    def res_kn(self):
        query_type = self.norm_query_type(oa.openai_chat("gpt-4.1-mini",gp.kn_class_prompt(self.userText)))
        if query_type == None:
            return self.res_invalid_query()
        else:
            return self.res_valid_query(query_type)

    def norm_query_type(self,text):
        match = re.search(r'\d', text)
        if match:
            queryType = int(match.group())
            if queryType == 1 or queryType == 2:
                return queryType
        else:
            return None

    def res_invalid_query(self):
        return ["無効な質問です。質問内容を変えてもう一度送信してください"]

    def res_valid_query(self,query_type):
        cont  = self.norm_res_cont(oa.openai_chat("gpt-4.1",gp.kl_response_prompt(query_type,self.userText)))
        if cont is not None:
            cont = [cont]
            # perse_cont = [line for line in cont.split('\n') if line]
            cont.append("※AIは誤った情報を回答をする場合があります。\n個別の保険商品などはご自身で調べ、正しい情報を得るようにしてください")
            return cont
        else:
            return ["申し訳ございません。適切な応答を生成できませんでした"]

    def norm_res_cont(self,text):
        pattern = r'<response>(.*?)</response>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def res_qa(self):
        qa_list, qa_dict = ic.search_index(self.userText)
        q,a,url = ic.assist_ai(self.userText,qa_list,qa_dict)
        if q and a:
            qa_text = "Q." + q + "\nA." + a
        else:
            qa_text = ["ユーザーの質問に関連するQA情報はありません"]
        res = self.norm_answer_cont(oa.openai_chat("gpt-4.1",gp.get_qa_prompt(self.userText,qa_text)))
        if res is not None:
            res = [res]
            # perse_res = [line for line in res.split('\n') if line]
            res.append("参考QA:\n" + url)
            return res
        else:
            res = ["応答の生成に失敗しました。再度、ご質問をお伝えください"]
            return res
    
    def norm_answer_cont(self,text):
        pattern = r'<answer>(.*?)</answer>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def res_yo(self):
        prompt = gp.get_searchYoutube_prompt(self.userText)
        searchTerms = self.norm_term_cont(oa.openai_chat("gpt-4.1-mini",prompt))
        if not searchTerms:
            res = ["検索ワードの生成に失敗しました。再度、ご要望をお伝えください"]
            return res
        # youtube data api にて検索結果を表示
        result,textResult = ya.search_videos(searchTerms)
        if not result:
            res = ["YouTube動画検索に失敗しました。再度、ご要望をお伝えください"]
            return res
        
        # キューの内容に最も適切な検索結果を判断
        videoNum = self.norm_video_num(oa.openai_chat("gpt-4.1-mini",gp.get_judg_prompt(self.userText, textResult)))
        if not videoNum:
            res = ["YouTube動画検索に失敗しました。再度、ご要望をお伝えください"]
            return res
        res = self.gen_video_res(result,videoNum,searchTerms)
        return res

    def norm_term_cont(self,text):
        pattern = r'<search_terms\d+>(.*?)</search_terms\d+>'
        matches = re.findall(pattern, text, re.DOTALL)
        search_terms = [match.strip() for match in matches]
        return search_terms if search_terms else None

    def norm_video_num(self,text):
        pattern = r'<(first|second|third)_selected_video>\s*(.*?)\s*</\1_selected_video>'
        matches = re.findall(pattern, text, re.DOTALL)
        video_numbers = []
        for match in matches:
            content = match[1]
            number_match = re.search(r'\d+', content)
            if number_match:
                video_numbers.append(int(number_match.group()))
        return video_numbers if video_numbers else None

    def gen_video_res(self,all_videos,videoNum,searchTerms) -> list:
        res = []
        res.append("以下のキーワードでYouTube動画を検索しました\n\n"+"\n".join(searchTerms)+"\n\n検索結果は以下の通りです")
        # 動画番号をキー、URLを値とする辞書を作成
        video_dict = {video["num"]: video["url"] for video in all_videos}
        for num in videoNum:
            url = video_dict.get(num)
            if url:
                res.append(url)
        return res

    def res_gs(self):
        convs = self.get_convs_text(self.userData['conversations'])
        prompt = gp.get_gs_prompt(convs,self.userText)
        res = self.norm_gs_res(oa.openai_chat("gpt-4.1",prompt))
        if res:
            # 会話履歴を更新する
            fa.update_history(db,self.userId,data_limit,user=self.userText,assistant=res)
            res = [res]
            # perse_res = [line for line in res.split('\n') if line]
            return res
        else:
            return ["応答の取得に失敗しました。再度、ご要望をお伝えください"]
    
    def get_convs_text(self,convs):
        text_list = []
        for conv in convs:
            text = f"""
<speaker>{conv['speaker']}</speaker>
<message>{conv['content']}</message>"""
            text_list.append(text)
        return "".join(text_list)

    def norm_gs_res(self,text):
        pattern = r'<response>(.*?)</response>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def res_tr(self):
        transfer_status = self.userData.get('transfer_status', 0)
        # transfer_statusに基づく処理
        if transfer_status == 1:
            return self.process_insured_info()
        elif transfer_status == 2:
            return self.process_current_insurance()
        elif transfer_status == 3:
            return self.process_target_insurance()
        elif transfer_status == 4:
            return self.process_search_insurance()
        elif transfer_status == 5:
            return self.process_create_proposal()
        elif transfer_status == 6:
            return self.process_summary_proposal()
        elif transfer_status ==7:
            return ["提案が終了しました。\n\n新たな条件で提案を作成する場合は再度、メニュー「乗換の提案」ボタンをタップしてください"]
    
    def res_ta(self):
        talk_status = self.userData.get('talk_status', 0)
        # talk_statusに基づく処理を追加
        if talk_status == 1:
            return self.process_talk_info()
        elif talk_status == 2:
            return self.process_mapping_proposal()
        elif talk_status == 3:
            return self.process_talk_proposal()
        elif talk_status == 4:
            return self.process_talk_summary_proposal()
        elif talk_status == 5:
            return ["提案が終了しました。\n\n新たな条件で提案を作成する場合は再度、メニュー「話しかけ方」ボタンをタップしてください"]

    def process_insured_info(self):
        """被保険者情報を処理する関数"""
        try:
            # Firestoreに保存
            fa.update_insurance_state(db, self.userId, 
                transfer_status=2,
                info_type='insured_info',
                info_data={'info': self.userText}
            )
            
            return ["ありがとうございます。\n次に、お客様が現在ご加入されている保険会社名と保険商品名、月々の保険料を教えてください。\n\n例：「A生命保険、XX終身保険、15,000円」"]
        except Exception as e:
            print(f"Error in process_insured_info: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]

    def extract_insurance_info(self):
        """保険会社名、保険商品名、保険料を抽出する共通関数"""
        try:
            # 保険料を抽出（数字と単位「円」を含む部分を探す）
            premium_match = re.search(r'(\d{1,3}(,\d{3})*|\d+)\s*円', self.userText)
            premium = premium_match.group(1) if premium_match else None

            if not premium:
                return None, None, None

            # AIウェブサーチで保険会社と商品名を調査
            search_prompt = gp.get_insurance_search_prompt(self.userText)
            search_result = oa.openai_search("gpt-4o-search-preview", search_prompt, context_size="high")

            # 検索結果から情報を抽出
            company_match = re.search(r'<company_name>\s*(.*?)\s*</company_name>', search_result, re.DOTALL)
            product_match = re.search(r'<product_name>\s*(.*?)\s*</product_name>', search_result, re.DOTALL)

            company_name = company_match.group(1) if company_match else None
            product_name = product_match.group(1) if product_match else None

            if company_name == 'None' or product_name == 'None':
                return None, None, None

            return company_name, product_name, premium
        except Exception as e:
            print(f"Error in extract_insurance_info: {str(e)}")
            return None, None, None

    def process_current_insurance(self):
        """現在の保険情報を処理する関数"""
        try:
            # 共通関数を使用して保険情報を抽出
            company_name, product_name, premium = self.extract_insurance_info()

            if not company_name or not product_name or not premium:
                return ["申し訳ありません。入力形式が誤っているか、該当する保険会社名・商品名が見つかりませんでした。\n保険会社名、保険商品名の正しい名称と、月々の保険料を以下の形式で教えてください。\n\n例：「A生命保険、XX終身保険、15,000円」"]

            # Firestoreに保存
            fa.update_insurance_state(db, self.userId,
                transfer_status=3,
                info_type='current_insurance',
                info_data={
                    'company_name': company_name,
                    'product_name': product_name,
                    'premium': premium
                }
            )
            
            # リプライメッセージを作成
            messages = [
                f"ご提供いただいた情報から、以下の保険商品を特定しました：\n・保険会社：{company_name}\n・商品名：{product_name}\n・保険料：{premium}円",
                "次に、乗り換え提案したい保険会社名と保険商品名、希望する月々の保険料を教えてください。\n\n例：「B生命保険、YY終身保険、12,000円」"
            ]
            
            return messages

        except Exception as e:
            print(f"Error in process_current_insurance: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。\n再度、保険会社名、保険商品名、月々の保険料を以下の形式で教えてください。\n\n例：「A生命保険、XX終身保険、15,000円」"]

    def process_target_insurance(self):
        """乗り換え先の保険情報を処理する関数"""
        try:
            # 共通関数を使用して保険情報を抽出
            company_name, product_name, premium = self.extract_insurance_info()

            if not company_name or not product_name or not premium:
                return ["入力形式が誤っているか、該当する保険会社名・商品名が見つかりませんでした。\n保険会社名、保険商品名の正しい名称と、月々の保険料を以下の形式で教えてください。\n\n例：「B生命保険、YY終身保険、12,000円」"]

            # Firestoreに保存
            fa.update_insurance_state(db, self.userId,
                transfer_status=4,
                info_type='target_insurance',
                info_data={
                    'company_name': company_name,
                    'product_name': product_name,
                    'premium': premium
                }
            )
            
            # リプライメッセージを作成
            messages = [
                f"ご提供いただいた情報から、以下の保険商品を特定しました：\n・保険会社：{company_name}\n・商品名：{product_name}\n・保険料：{premium}円",
                "次に、これらの保険商品の情報を収集します","これには ※1分程度かかる※ 場合がございます。\n\n実行してもよろしいでしょうか？\n\n「はい」か「いいえ」で回答してください"
            ]
            
            return messages

        except Exception as e:
            print(f"Error in process_target_insurance: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。\n保険会社名、保険商品名、月々の保険料を以下の形式で教えてください。\n\n例：「B生命保険、YY終身保険、12,000円」"]

    def process_search_insurance(self):
        """保険商品検索を実行する関数"""
        if self.userText == 'はい':
            return self.excute_search_insurance()
        else:
            return self.cancel_search_insurance()

    def excute_search_insurance(self):
        """保険商品を検索する関数"""
        try:
            # 現在の保険情報の処理
            current_insurance = self.userData.get('insurance_current_insurance')
            current_result = self.search_insurance_info(current_insurance)

            message = ["保険商品の情報を取得しました！："]
            if current_result:
                content = current_result['content']
                current_insurance_info = {
                    'content': current_result.get('content', None),
                    'company_name': current_result.get('company', None),
                    'insurance_name': current_result.get('insurance_name', None),
                    'premium': current_insurance.get('premium', None)
                }
                text = f"【現在の保険商品の情報】\n{content}\n\n"
                message.append(text)
            # 目標の保険情報の処理
            target_insurance = self.userData.get('insurance_target_insurance')
            target_result = self.search_insurance_info(target_insurance)
            
            if target_result:
                content = target_result['content']
                target_insurance_info = {
                    'content': target_result.get('content', None),
                    'company_name': target_result.get('company', None),
                    'insurance_name': target_result.get('insurance_name', None),
                    'premium': target_insurance.get('premium', None)
                }
                text = f"【提案先の保険商品の情報】\n{content}"
                message.append(text)

            if not all([current_result, target_insurance]):
                return ["申し訳ありません。情報収集に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]

            # Firestoreの状態を更新
            fa.update_insurance_state(db, self.userId, 
                transfer_status=5, # 乗り換え提案を作成
                current_insurance_info=current_insurance_info,
                target_insurance_info=target_insurance_info
            )
            message.append("この情報をもとに、乗り換え提案トークを作成できます。\n\n実行しますか？\n\n「はい」か「いいえ」で回答してください")
            return message
        except Exception as e:
            logging.error(f"Error in excute_search_insurance: {str(e)}")
            return ["申し訳ありません。調査結果の取得に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]

    def search_insurance_info(self, insurance_data):
        """
        保険情報を検索し、最も適切な結果を返す関数
        
        Args:
            insurance_data (dict): 保険情報を含む辞書 (company_name, product_nameを含む)
            db: Firestoreデータベースインスタンス
            oa: OpenAIアダプターインスタンス
            
        Returns:
            dict or None: 検索された保険情報。見つからない場合はNone
        """
        if not insurance_data:
            return None
            
        search_text = f"{insurance_data['company_name']}の{insurance_data['product_name']}"
        vector = oa.embedding([search_text])[0]
        search_results = fa.get_insurance_info(db, vector, 10)
        
        # 検索結果のテキスト化（番号付き）
        search_text_numbered = "\n".join([
            f"{i}. {result['company']}の{result['insurance_name']}\n説明: {result['content'][:50]}..." 
            for i, result in enumerate(search_results, 1)
        ])
        
        # AI による検証
        verify_prompt = gp.get_insurance_verification_prompt(search_text_numbered, search_text)
        verification_response = oa.openai_chat("gpt-4.1", verify_prompt)
        
        if verification_response:
            match = re.search(r'<result_number>\s*(\d+|None)\s*</result_number>', verification_response)
            if match:
                result_number = match.group(1)
                if result_number != "None":
                    # 選択された保険情報を取得
                    selected_insurance = search_results[int(result_number) - 1]
                    # contentの内容を評価
                    content_verify_prompt = gp.get_insurance_content_verification_prompt(selected_insurance['content'])
                    content_verification = oa.openai_chat("gpt-4.1", content_verify_prompt)
                    # 内容が十分な場合は選択された保険情報を返す
                    if content_verification and 'true' in content_verification.lower():
                        return selected_insurance
                    # 内容が不十分な場合は新しい情報を取得
                    else:
                        return self.get_insurance_details(insurance_data['company_name'], insurance_data['product_name'])
                else:
                    return self.get_insurance_details(insurance_data['company_name'], insurance_data['product_name'])
        
        return None


    def get_insurance_details(self, company_name, product_name):
        """
        保険商品の詳細情報をAIウェブサーチで取得し、データベースに保存する関数
        
        Args:
            company_name (str): 保険会社名
            product_name (str): 商品名
            
        Returns:
            dict: 保険商品の詳細情報を含む辞書。以下のキーを含む:
                - company: 保険会社名
                - insurance_name: 保険商品名
                - content: 商品の詳細内容
        """
        try:
            # プロンプトの準備
            search_prompt = gp.get_insurance_product_search_details_prompt()
            prompt = f"{search_prompt}\n\n保険会社名: {company_name}\n保険商品名: {product_name}"

            # AIによる詳細情報の収集
            response = oa.openai_search(
                openai_model="gpt-4o-search-preview",
                prompt=prompt,
                context_size="high"
            )
            
            if not response:
                raise ValueError("Failed to get response from AI search")

            # 商品詳細情報の抽出
            content_start = response.find("<product_info>")
            content_end = response.find("</product_info>")

            if content_start < 0 or content_end < 0:
                raise ValueError("Failed to extract product details from response")

            content = response[content_start + len("<product_info>"):content_end].strip()

            if not content:
                raise ValueError("Empty content extracted from response")

            # 保険商品情報を構造化
            insurance_info = {
                "company": company_name,
                "insurance_name": product_name,
                "content": content,
            }
            # 保険情報DBエンドポイントへ送信
            try:
                response = requests.post(INSURANCE_DB_URL + "/insurance", json=insurance_info)
                return insurance_info
            
            except Exception as e:
                logging.error(f"Error in send_insurance_info: {str(e)}")
                return None
        
        except Exception as e:
            logging.error(f"Error in get_insurance_details: {str(e)}")
            return None

    def cancel_search_insurance(self):
        fa.update_insurance_state(db, self.userId, transfer_status=1, should_delete=True)
        
        return [
            "保険商品の情報収集をキャンセルしました。",
            "はじめから乗り換え提案の生成をやり直す場合は、想定されるお客様の年齢と性別を教えてください。\n\nまた、その他の補足情報があれば教えてください",
            "例：\n年齢:45歳\n性別:男性\n職業:会社員\n保険の目的:死亡保障と子供の積立、老後の資産\n死亡受取:配偶者　など"
        ]

    def process_create_proposal(self):
        """保険乗り換えトークを生成する関数"""
        if self.userText == 'はい':
            return self.create_proposal()
        else:
            return self.cancel_proposal()

    def create_proposal(self):
        """保険乗り換えトークを生成する関数"""
        try:
            # 保険情報の取得
            current_result = self.userData.get('insurance_current_insurance')
            target_result = self.userData.get('insurance_target_insurance')

            if not current_result or not target_result:
                return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # 保険情報が揃っている場合、提案を作成
            insured_info = self.userData.get('insurance_insured_info', {})
            
            # 提案生成プロンプトの作成
            proposal_prompt = gp.get_insurance_proposal_prompt(
                insured_info=insured_info,
                current_insurance=current_result,
                target_insurance=target_result
            )
            
            # 提案の生成
            proposal_response = oa.openai_chat("gpt-4.1", proposal_prompt)
            
            if proposal_response:
                # 各セクションを抽出
                sections = {
                    # '特徴解説': re.search(r'<feature_analysis>(.*?)</feature_analysis>', proposal_response, re.DOTALL),
                    'メリット・デメリット分析': re.search(r'<merit_demerits>(.*?)</merit_demerits>', proposal_response, re.DOTALL),
                    # '評価': re.search(r'<evaluation_score>(.*?)</evaluation_score>', proposal_response, re.DOTALL),
                    '提案方法': re.search(r'<proposal_method>(.*?)</proposal_method>', proposal_response, re.DOTALL),
                    '総評と反論': re.search(r'<overall_evaluation>(.*?)</overall_evaluation>', proposal_response, re.DOTALL)
                }
                
                # 各セクションのテキストを抽出し、整形
                proposal_sections = {}
                for title, match in sections.items():
                    if match:
                        proposal_sections[title] = match.group(1).strip()
                    else:
                        proposal_sections[title] = "情報なし"
                
                # 提案内容を整形
                formatted_proposal = [
                    "乗り換え提案の作成が完了しました！",
                    "\n\n【1. 各保険のメリット・デメリット分析】\n" + proposal_sections['メリット・デメリット分析']
                    + "\n\n【2. 提案方法】\n" + proposal_sections['提案方法']
                    + "\n\n【3. 総評と反論】\n" + proposal_sections['総評と反論'],
                    "※AIによる提案内容は参考情報です。\n\n提案はお客様の状況や会話内容に応じて、適切にアレンジしてください。\n\nまた、実際の保険商品の詳細や正確な情報は、各保険会社の公式情報をご確認ください。",
                ]
                # "【1. 各保険の特徴解説】\n" + proposal_sections['特徴解説']
                # + "\n\n【3. 各保険の評価】\n" + proposal_sections['評価']
                proposal_text = "\n".join(formatted_proposal)
                
                # 状態を更新
                fa.update_insurance_state(
                    db, 
                    self.userId, 
                    transfer_status=6,
                    proposal_text=proposal_text,
                )
                formatted_proposal.append("この提案を要約しますか？\n「はい」か「いいえ」で回答してください")
                
                logging.info(f"Sending insurance proposal to user: {self.userId}")

                return formatted_proposal
                    
            # 提案作成に失敗した場合はエラーメッセージを表示
            error_message = ["申し訳ありません。提案の作成に失敗しました。\n\n再実行しますか？「はい」か「いいえ」で回答してください"]
            logging.error(f"Failed to create proposal for user: {self.userId}")
            la.push_message(LINE_ACCESS_TOKEN, self.userId, error_message)
            return []

        except Exception as e:
            logging.error(f"Error in create_proposal: {str(e)}")
            error_message = ["申し訳ありません。エラーが発生しました。\n\n再実行しますか？「はい」か「いいえ」で回答してください"]
            la.push_message(LINE_ACCESS_TOKEN, self.userId, error_message)
            return []
        
    def cancel_proposal(self):
        """保険商品の乗り換え提案をキャンセルし、初期状態に戻す関数"""
        # transfer_statusを1に設定し、保険情報を削除
        fa.update_insurance_state(db, self.userId, transfer_status=1, should_delete=True)
        
        return [
            "乗り換え提案トークの作成をキャンセルしました。",
            "はじめから乗り換え提案の生成をやり直す場合は、想定されるお客様の年齢と性別を教えてください。詳しいほど、より正確な情報をご提供できます。\n\nまた、その他の補足情報があれば教えてください",
            "例：\n年齢:45歳\n性別:男性\n職業:会社員\n保険の目的:死亡保障と子供の積立、老後の資産\n死亡受取:配偶者　など"
        ]

    def process_summary_proposal(self):
        """保険乗り換えトークの要約を生成する関数"""
        if self.userText == 'はい':
            return self.create_summary_proposal()
        else:
            return self.cancel_summary_proposal()

    def create_summary_proposal(self):
        """保険乗り換えトークの要約を生成する関数"""
        try:
            proposal_text = self.userData.get('proposal_text')
            if not proposal_text:
                return ["申し訳ありません。提案内容の取得に失敗しました"]
        
            # 提案内容を要約するプロンプトを作成
            summary_prompt = gp.get_insurance_summary_proposal_prompt(proposal_text)

            # AIによる要約生成
            summary_response = oa.openai_chat("gpt-4.1", summary_prompt)

            if not summary_response:
                return ["申し訳ありません。要約の生成に失敗しました。\n\n再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # 要約内容を整形
            summary_text = re.search(r'<summary>(.*?)</summary>', summary_response, re.DOTALL)
            if not summary_text:
                return ["申し訳ありません。要約の抽出に失敗しました。\n\n再実行しますか？「はい」か「いいえ」で回答してください"]
            
            summary = summary_text.group(1).strip()

            # 状態を更新
            fa.update_insurance_state(
                db, 
                self.userId, 
                transfer_status=7,
                should_delete=True
            )
            
            return [
                "保険乗り換えトークの要約が完了しました！",
                "要約内容：\n" + summary,
                "※AIによる提案内容は参考情報です。\n\n提案はお客様の状況や会話内容に応じて、適切にアレンジしてください。\n\nまた、実際の保険商品の詳細や正確な情報は、各保険会社の公式情報をご確認ください。"
            ]
        
        except Exception as e:
            logging.error(f"Error in create_summary_proposal: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。\n\n再実行しますか？「はい」か「いいえ」で回答してください"]
    
    def cancel_summary_proposal(self):
        """保険乗り換えトークの要約をキャンセルし、初期状態に戻す関数"""
        # transfer_statusを1に設定し、保険情報を削除
        fa.update_insurance_state(db, self.userId, transfer_status=7, should_delete=True)
        
        return [
            "乗り換え提案トークの要約をキャンセルしました。"
        ]

    def process_talk_info(self):
        """トークモードでの個人情報を処理する関数"""
        try:
            # テキストをベクトル化
            vector = oa.embedding([self.userText])[0]
            
            # ベクトル検索で関連記事を取得
            search_results = fa.get_article_info(db, vector, 5)  # 上位5件を取得
            
            isNotRelated = True
            if search_results:
                isNotRelated = False
            
            # 検索結果からcontentのリストを作成
            contents = [result['content'] for result in search_results]
            
            # AIによる関連性の評価
            verify_prompt = gp.get_talk_content_verification_prompt(self.userText, contents)
            verification_response = oa.openai_chat("gpt-4.1", verify_prompt)
            
            # 関連性のある記事番号を抽出
            relevant_numbers = []
            if not verification_response:
                return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]
            match = re.search(r'<relevant_numbers>\s*(.*?)\s*</relevant_numbers>', verification_response, re.DOTALL)
            if not match:
                return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]
            numbers_str = match.group(1).strip()
            if numbers_str.lower() == 'none':
                isNotRelated = True
            else:
                # カンマ区切りの番号をリストに変換
                relevant_numbers = [int(num.strip()) for num in numbers_str.split(',')]
            
            # 返信メッセージを作成
            messages = ["ありがとうございます。\nご提供いただいた情報を保存しました"]
            messages.append("情報をもとに、保険提案につながりそうな話題を調べました！：")
            
            # 関連記事情報を格納するリスト
            related_articles = []
            
            if not relevant_numbers:
                isNotRelated = True
            
            topic_list = []
            if isNotRelated:
                # AIによる話題生成（ネット検索モデルを使用）
                generate_prompt = gp.get_talk_topic_generation_prompt(self.userText)
                generated_response = oa.openai_search("gpt-4o-search-preview", generate_prompt, context_size="medium")
                
                if not generated_response:
                    return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]
                
                # 生成された話題を抽出
                topics = []
                for topic_num in ['first', 'second', 'third']:
                    topic_match = re.search(f'<{topic_num}_topic>(.*?)</{topic_num}_topic>', generated_response, re.DOTALL)
                    if topic_match:
                        topic = topic_match.group(1).strip()
                        if topic:
                            topics.append(topic)
                
                if not topics:
                    return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]
                
                # 生成された話題をメッセージに追加
                for i, topic in enumerate(topics, 1):
                    topic_list.append(f"{i}. {topic}")
                    related_articles.append({'content': topic})
                messages.append("\n\n".join(topic_list))
            else:
                # 関連性のある記事を番号付きで追加
                for i, num in enumerate(relevant_numbers, 1):
                    if 1 <= num <= len(contents):
                        content = contents[num-1]
                        topic_list.append(f"{i}. {content}")
                        related_articles.append({'content': content})
                messages.append("\n\n".join(topic_list))
            
            messages.append("この内容をもとに、おすすめの保険種類と提案セリフの生成ができます。実行しますか？\n「はい」か「いいえ」で回答してください")
            
            # Firestoreに個人情報と関連記事を保存
            fa.update_talk_state(db, self.userId, 
                talk_status=2,  # マッピング作成/続行確認
                personal_info=self.userText,
                related_articles=related_articles
            )
            
            return messages
            
        except Exception as e:
            logging.error(f"Error in process_talk_info: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。再度メッセージを送信してください"]

    def process_mapping_proposal(self):
        """トークモードでの保険提案マッピングを処理する関数"""
        if self.userText == 'はい':
            return self.create_mapping_proposal()
        else: # mesText == 'いいえ'
            return self.cancel_mapping_proposal()
        
    def create_mapping_proposal(self):
        """
        個人情報と関連記事から保険提案トークのマッピングを生成する
        
        Args:
            userId (str): ユーザーID
            user_data (dict): ユーザーデータ
            
        Returns:
            list: リプライメッセージのリスト
        """
        try:
            # 個人情報と関連記事を取得
            personal_info = self.userData.get('talk_personal_info')
            related_articles = self.userData.get('talk_related_articles', [])
            
            if not personal_info or not related_articles:
                return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # 各記事に対してマッピングを生成
            talk_mappings = []
            for article in related_articles:
                content = article.get('content')
                if not content:
                    continue
                    
                # AIによるマッピング生成
                prompt = gp.get_talk_mapping_prompt(personal_info, content)
                mapping_response = oa.openai_chat("gpt-4.1", prompt)
                
                if not mapping_response:
                    continue
                    
                # 各要素を正規表現で抽出
                title_match = re.search(r'<title>(.*?)</title>', mapping_response, re.DOTALL)
                category_match = re.search(r'<insurance_category>(.*?)</insurance_category>', mapping_response, re.DOTALL)
                question_match = re.search(r'<needs_question>(.*?)</needs_question>', mapping_response, re.DOTALL)
                hook_match = re.search(r'<hook_phrase>(.*?)</hook_phrase>', mapping_response, re.DOTALL)
                
                if all([title_match, category_match, question_match, hook_match]):
                    mapping = {
                        'content': content,
                        'title': title_match.group(1).strip(),
                        'insurance_category': category_match.group(1).strip(),
                        'needs_question': question_match.group(1).strip(),
                        'hook_phrase': hook_match.group(1).strip()
                    }
                    talk_mappings.append(mapping)
            
            if not talk_mappings:
                return ["申し訳ありません。生成に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # Firestoreの状態を更新
            fa.update_talk_state(db, self.userId, 
                talk_status=3, # トーク生成中/続行確認
                talk_mappings=talk_mappings
            )
            
            # レスポンスメッセージを生成
            messages = ["生成が完了しました！："]
            mapping_text = []
            for i, mapping in enumerate(talk_mappings, 1):
                message = f"{i}. {mapping['title']}\n"
                message += f"・おすすめの保険種類：{mapping['insurance_category']}\n"
                message += f"・ニーズ喚起セリフ：{mapping['needs_question']}\n"
                message += f"・切込みセリフ：{mapping['hook_phrase']}\n\n"
                mapping_text.append(message)
            messages.append("\n".join(mapping_text))
                
            messages.append("この内容で、さらに保険提案トークを想定できます。実行しますか？\n「はい」か「いいえ」で回答してください")
            
            return messages
            
        except Exception as e:
            logging.error(f"Error in create_talk_proposal: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]

    def cancel_mapping_proposal(self):
        """トークモードでの保険提案セリフをキャンセルする関数"""
        fa.update_talk_state(db, self.userId, talk_status=1, should_delete=True)
        
        return [
            "保険提案セリフ作成をキャンセルしました。",
            "やり直す場合は、想定される被保険者の年齢と性別、その他の保険提案の参考になりそうな情報があれば教えてください。\n\n詳しいほど、より正確な情報をご提供できます。",
            "例：\n年齢:30代\n性別:女性\n家族構成:夫婦2人\n職業:会社員\n居住地:東京都　など",
            "終了する場合は、別のメニューを選択してください"
        ]

    def process_talk_proposal(self):
        """トークモードでの保険提案トークを処理する関数"""
        if self.userText == 'はい':
            return self.create_talk_proposal()
        else: # mesText == 'いいえ'
            return self.cancel_talk_proposal()
        
    def create_talk_proposal(self):
        """
        保険提案トークを生成する関数
        
        Args:
            userId (str): ユーザーID
            user_data (dict): ユーザーデータ
            
        Returns:
            list: リプライメッセージのリスト
        """
        try:
            # 必要なデータを取得
            personal_info = self.userData.get('talk_personal_info')
            related_articles = self.userData.get('talk_related_articles', [])
            talk_mappings = self.userData.get('talk_mappings', [])
            
            if not personal_info or not related_articles or not talk_mappings:
                return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # 各記事に対する提案トークを生成
            all_proposals = []
            for i, article in enumerate(related_articles):
                content = article.get('content')
                mapping = talk_mappings[i]
                
                # プロンプトを生成
                prompt = gp.get_talk_proposal_prompt(personal_info, content, mapping)
                
                # AIによる会話生成
                conversation = oa.openai_chat("gpt-4.1", prompt)
                
                if not conversation:
                    continue
                    
                # 各フェーズの会話を抽出
                phases = {}
                for phase in ['introduction', 'news_topic', 'needs_awareness', 'proposal']:
                    pattern = f'<{phase}>(.*?)</{phase}>'
                    match = re.search(pattern, conversation, re.DOTALL)
                    if match:
                        phases[phase] = match.group(1).strip()
                
                # 提案トークを構造化
                proposal = {
                    'title': mapping['title'],
                    'insurance': mapping['insurance_category'],
                    'phases': phases
                }
                all_proposals.append(proposal)
            
            if not all_proposals:
                return ["申し訳ありません。生成に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            # レスポンスメッセージを生成
            messages = ["保険提案トークの生成が完了しました！"]
            
            talk_list = []
            talk_text = ""
            for i, proposal in enumerate(all_proposals, 1):
                talk_list.append(f"\n【提案パターン{i}】\n■ タイトル：{proposal['title']}\n■ 提案保険：{proposal['insurance']}")
                talk_list.append("\n# 1. 導入")
                talk_list.append(proposal['phases'].get('introduction', '会話生成に失敗しました'))
                talk_list.append("\n# 2. 時事ネタ")
                talk_list.append(proposal['phases'].get('news_topic', '会話生成に失敗しました'))
                talk_list.append("\n# 3. ニーズ喚起")
                talk_list.append(proposal['phases'].get('needs_awareness', '会話生成に失敗しました'))
                talk_list.append("\n# 4. 切込み提案")
                talk_list.append(proposal['phases'].get('proposal', '会話生成に失敗しました'))
                talk_list.append("\n" + "="*23)
                talk_text += "\n".join(talk_list)
                talk_list = []
            messages.append(talk_text)

            # 状態を更新
            fa.update_talk_state(
                db, 
                self.userId, 
                talk_status=4, # 要約を提案している状態
                talk_text=talk_text
                )
            
            messages.append("※AIによる提案内容は参考情報です。実際の提案時は、お客様の状況や会話内容に応じて適切にアレンジしてください。")
            messages.append("この提案を要約しますか？\n「はい」か「いいえ」で回答してください")

            return messages
            
        except Exception as e:
            logging.error(f"Error in create_talk_proposal: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]

    def cancel_talk_proposal(self):
        """トークモードでの保険提案トークをキャンセルする関数"""
        fa.update_talk_state(db, self.userId, talk_status=1, should_delete=True)
        
        return [
            "保険提案トーク作成をキャンセルしました。",
            "やり直す場合は、想定される被保険者の年齢と性別、その他の保険提案の参考になりそうな情報があれば教えてください。\n\n詳しいほど、より正確な情報をご提供できます。",
            "例：\n年齢:30代\n性別:女性\n家族構成:夫婦2人\n職業:会社員\n居住地:東京都　など"
        ]

    def process_talk_summary_proposal(self):
        """トークモードでの保険提案トークの要約を処理する関数"""
        if self.userText == 'はい':
            return self.create_talk_summary_proposal()
        else: # mesText == 'いいえ'
            return self.cancel_talk_summary_proposal()
    
    def create_talk_summary_proposal(self):
        """トークモードでの保険提案トークの要約を生成する関数"""
        try:
            talk_text = self.userData.get('talk_text')
            if not talk_text:
                return ["申し訳ありません。提案内容の取得に失敗しました"]
        
            summary_prompt = gp.get_talk_summary_proposal_prompt(talk_text)
            summary_response = oa.openai_chat("gpt-4.1", summary_prompt)
            
            if not summary_response:
                return ["申し訳ありません。要約の生成に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            summary_match = re.search(r'<summary>(.*?)</summary>', summary_response, re.DOTALL)
            if not summary_match:
                return ["申し訳ありません。要約の抽出に失敗しました。再実行しますか？「はい」か「いいえ」で回答してください"]
            
            new_summary = summary_match.group(1).strip()
            
            # 状態を更新
            fa.update_talk_state(
                db, 
                self.userId, 
                talk_status=5, # 提案が完了した状態
                should_delete=True
                )
            
            return [
                "保険提案トークの要約が完了しました！",
                "要約内容：\n" + new_summary
            ]
        
        except Exception as e:
            logging.error(f"Error in create_talk_summary_proposal: {str(e)}")
            return ["申し訳ありません。エラーが発生しました。再実行しますか？「はい」か「いいえ」で回答してください"]
        
    def cancel_talk_summary_proposal(self):
        """トークモードでの保険提案トークの要約をキャンセルする関数"""
        fa.update_talk_state(db, self.userId, talk_status=5, should_delete=True)
        
        return [
            "保険提案トークの要約をキャンセルしました"
        ]
    
    def res_rp(self):
        if self.userData['isAlreadyRP']:
            return self._process_rp()
        else:
            return ["営業ロープレは終了しています。メニューから「開始＆リセット」をクリックして開始してください"]

    def _process_rp(self):
        """RPの会話を処理するメソッド"""
        rp_setting = self.userData['rp_setting']
        rp_summary = self.userData.get('rp_summary', None)
        history = self.userData.get('rp_history', [])
        full_history = self.userData.get('rp_full_history', [])
        if not history:
            history_text = ""
        else:
            history_text = self.get_rphis_text(history)
        if not full_history:
            full_history_text = ""
        else:
            full_history_text = self.get_rphis_text(full_history)

        # 会話履歴の数をチェック
        history_count = len(history)
        should_summarize = False

        # 要約が必要かどうかを判断
        if rp_summary is None and history_count >= 10:
            should_summarize = True
        elif rp_summary is not None and history_count >= 9:
            should_summarize = True

        if should_summarize:
            # 要約を生成
            summary_prompt = gp.get_rp_summary_prompt(history_text, rp_summary)
            summary_response = oa.openai_chat("gpt-4.1", summary_prompt)
            
            if not summary_response:
                return ["申し訳ありません。エラーが発生しました。もう一度お試しください"]
            
            # 要約文を抽出
            summary_match = re.search(r'<information>(.*?)</information>', summary_response, re.DOTALL)
            if not summary_match:
                return ["申し訳ありません。エラーが発生しました。もう一度お試しください"]
            
            new_summary = summary_match.group(1).strip()
            
            # 会話履歴をリセットし、要約文を保存
            fa.reset_rp_history(db, self.userId, isResetHistory=True)
            fa.update_rp_history(db, self.userId, rp_data_limit, summary=new_summary)
            
            # 履歴を更新した後、historyを空にする（新しい会話の開始のため）
            history_text = ""
            rp_summary = new_summary

        # 保険提案の切込みかどうかを判定
        detection_prompt = gp.get_proposal_detection_prompt(history_text, self.userText, rp_summary)
        detection_response = oa.openai_chat("gpt-4.1", detection_prompt)
        
        if not detection_response:
            return ["応答の取得に失敗しました。再度、テキストを送信してください"]
        
        # 判定結果を抽出
        is_proposal_match = re.search(r'<is_proposal>\s*(true|false)\s*</is_proposal>', detection_response, re.DOTALL)
        if not is_proposal_match:
            return ["応答の取得に失敗しました。再度、テキストを送信してください"]
        
        if is_proposal_match.group(1).lower() == 'true':
            # 保険提案の受諾判定を実行
            acceptance_prompt = gp.get_proposal_acceptance_prompt(rp_setting, full_history_text)
            acceptance_response = oa.openai_chat("gpt-4.1", acceptance_prompt)
            
            if not acceptance_response:
                return ["応答の取得に失敗しました。再度、テキストを送信してください"]
            
            # 分析結果と判断を抽出
            analysis_match = re.search(r'<analysis>(.*?)</analysis>', acceptance_response, re.DOTALL)
            reaction_match = re.search(r'<reaction>(.*?)</reaction>', acceptance_response, re.DOTALL)
            
            if not analysis_match or not reaction_match:
                return ["応答の取得に失敗しました。再度、テキストを送信してください"]
            
            analysis = analysis_match.group(1).strip()
            reaction = reaction_match.group(1).strip()
            # 会話履歴を更新
            fa.update_rp_history(db, self.userId, rp_data_limit, salesperson=self.userText, customer=reaction)
            return [reaction]
        
        else: # 保険提案の切込みでない場合
            # 通常の会話処理
            prompt = gp.get_rp_prompt(rp_setting, history_text, self.userText, rp_summary)
            res = oa.openai_chat("gpt-4.1", prompt)

            if not res:
                return ["応答の取得に失敗しました。再度、テキストを送信してください"]
            # 会話履歴を更新
            fa.update_rp_history(db, self.userId, rp_data_limit, salesperson=self.userText, customer=res)
            return [res]
    
    def get_rphis_text(self,rp_history):
        text_list = []
        for conv in rp_history:
            text = f"""
<speaker>{conv['speaker']}</speaker>
<message>{conv['content']}</message>"""
            text_list.append(text)
        return "".join(text_list)
    
# if __name__ == "__main__":
#     userText = "猫の動画を調べてください"
#     prompt = gp.get_searchYoutube_prompt(userText)
#     response = oa.openai_chat("gpt-4.1-mini",prompt)
#     print("searchYoutubeResponse:",response)
#     searchTerms = extract_searchTerm_content(response)
#     if not searchTerms:
#         text = "検索ワードの生成に失敗しました。再度、ご要望をお伝えください"
#     # youtube data api にて検索結果を表示
#     result,textResult = ya.search_videos(searchTerms)
#     if not result:
#         text = "YouTube動画検索に失敗しました。再度、ご要望をお伝えください"
#     # キューの内容に最も適切な検索結果を判断
#     prompt = gp.get_judg_prompt(userText, textResult)
#     response = oa.openai_chat("gpt-4.1-mini",prompt)
#     print("judgeResponse:",response)
#     videoNum = extract_video_numbers(response)
#     if not videoNum:
#         text = "YouTube動画検索に失敗しました。再度、ご要望をお伝えください"
#     response_text = gen_response_text(result,videoNum,searchTerms)
#     print("responseText:",response_text)


# プランアップグレードした際にpending_actionが適用されているせいで、モード切替後のテキストがはい/いいえ待ちになる
# 
# %%
