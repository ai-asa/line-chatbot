# %%
import os
import re
import datetime
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

load_dotenv()
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
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
#     'price_1QNPiCRo65d8y4fNwGGoKq6y': '3980'
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
    "都内", "関東", "千葉県", "埼玉県", "大阪府", 
    "京都府", "愛知県", "福岡県", "北海道"
]

RP_INSURANCE_STATUS = [
    "保険未加入", 
    "生命保険のみ加入", 
    "医療保険のみ加入",
    "生命保険・医療保険に加入",
    "生命保険・医療保険・がん保険に加入"
]

RP_INSURANCE_DETAILS = [
    "月額保険料：5,000円", 
    "月額保険料：10,000円",
    "月額保険料：15,000円",
    "月額保険料：20,000円",
    "月額保険料：30,000円"
]

RP_PERSONALITIES = [
    "慎重派・保守的", "積極的・チャレンジ精神旺盛",
    "計画的・堅実", "直感的・決断が早い",
    "分析的・理論的", "感情的・共感力が高い",
    "リスク回避型", "バランス重視型"
]

def generate_rp_setting():
    """RPの設定をランダムに生成する"""
    setting = {
        "年齢": random.choice(RP_AGES),
        "性別": random.choice(RP_GENDERS),
        "世帯年収": random.choice(RP_ANNUAL_INCOMES),
        "家族構成": random.choice(RP_FAMILY_STRUCTURES),
        "居住地": random.choice(RP_LOCATIONS),
        "保険加入状況": random.choice(RP_INSURANCE_STATUS),
        "現在の保険料": random.choice(RP_INSURANCE_DETAILS),
        "性格": random.choice(RP_PERSONALITIES)
    }
    
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
    user_data = fa.get_user_data(db,userId,data_limit)
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

        user_data = fa.get_user_data(db,userId,data_limit)
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
    la.reply_to_line(LINE_ACCESS_TOKEN, replyToken, res)
    return True
    # except Exception as e:
    #     print(e)
    #     return False
    
def message_process(event,userId,user_data):
    mesText = event['message']['text']
    pending_action = user_data['pending_action']
    isRetryRP = user_data['isRetryRP']
    if pending_action:
        return sub_act(pending_action,mesText,userId,user_data)
    if isRetryRP:
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
    if mesText == 'はい':
        fa.reset_rp_history(db, userId, isResetHistory=True, isRetryRP=False)
        return ["会話履歴をリセットし、同じ設定で再度営業ロープレを開始します。", "====ここから開始====\n\nテキストを送信し、会話を開始してください..."]
    else:
        return close_rp(userId)
    
def close_rp(userId):
    fa.reset_rp_history(db, userId, isResetHistory=True, isAlreadyRP=False, isRetryRP=False)
    return ["営業ロープレを終了します。お疲れさまでした", "繰り返し練習し、営業力を高めましょう！"]

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
    return ["【開始通知】\n無料トライアルが開始されました", f"期間は{trial_start}から{trial_end}までです","期間中は中級プランと同様の機能をご利用いただけます", "ご利用いただき誠にありがとうございます"]

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
    # user_data = fa.get_user_data(db,userId,data_limit)
    return True
    # except Exception as e:
    #     print(e)
    #     return False
    
def event_unfollow(event,replyToken,userId):
    return True

def event_postback(event,replyToken,userId,user_data):
    pending_action = user_data['pending_action']
    isRetryRP = user_data['isRetryRP']
    if pending_action:
        return cancel_update_sub(userId)
    if isRetryRP:
        return close_rp(userId)
    postType = event['postback']['data']
    if postType in ['kn','qa','yo','gs','rps','rpr']:
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
    elif postType == "qa":
        judg,text = mode_qa(current_plan)
    elif postType == "yo":
        judg,text = mode_yo(current_plan)
    elif postType == "gs":
        judg,text = mode_gs(current_plan)
    elif postType == "rps":
        judg,text = mode_rps(current_plan,user_data)
    elif postType == "rpr":
        judg,text = mode_rpr(current_plan,user_data)
    if judg:
        fa.set_botType(db, userId, postType)
    return text

def mode_kn(current_plan):
    if current_plan == 'free':
        return False, ["本機能は各種プランへご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが保険の知識・提案方法に関して一問一答でお答えします"]

def mode_qa(current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが保険に関するQAデータベースに基づいてお答えします"]
    
def mode_yo(current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが知りたい情報についてYoutube動画をお調べします"]
    
def mode_gs(current_plan):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, ["【モード変更】\nゼロコンAIが会話形式で様々な質問、ご相談に対応します"]

def mode_rps(current_plan,user_data):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, rps_text(user_data)
    
def mode_rpr(current_plan,user_data):
    if current_plan in ['free','980']:
        return False, ["本機能は中級以上のプランにご契約いただくことでご利用いただけます"]
    else:
        return True, rpr_text(user_data)
    
def rps_text(user_data):
    """RPの設定を生成し、テキストを返す"""
    # RP設定を生成
    rp_setting = generate_rp_setting()
    
    if user_data['isAlreadyRP']:
        # 会話履歴とRP設定更新
        fa.reset_rp_history(db, user_data['userId'], isResetHistory=True, rp_setting=rp_setting)
        return ["これまでの営業ロープレの会話履歴と設定をリセットしました。\n\n新たに営業ロープレを開始します","====ここから開始====\n\nテキストを送信し、会話を開始してください..."]
    else:
        fa.set_initial_rp(db, user_data['userId'], isAlreadyRP=True, rp_setting=rp_setting)
        return ["【モード変更】\nゼロコンAIを相手に営業トレーニングを開始します", "ゼロコンAIが演じる顧客に対し、保険営業を行ってください！※顧客の設定はランダムに決められます", "メニューの「終了＆批評」ボタンをクリックすると営業ロープレを終了し、営業提案の内容を評価します",  "では、営業ロープレを開始します","====ここから開始====\n\nテキストを送信し、会話を開始してください..."]

def rpr_text(user_data):
    """
    営業ロープレの会話履歴を取得し、それを基にAIにて批評を行い、テキストを返す
    """
    if not user_data['isAlreadyRP']:
        return ["営業ロープレは開始されていません", "営業ロープレを開始するには、メニューの「開始＆リセット」ボタンをクリックしてください"]
    rp_history = user_data['rp_history']
    rp_setting = user_data['rp_setting']
    # res = norm_rpr_text(oa.openai_chat("gpt-4o",gp.get_rpr_prompt(rp_setting,rp_history)))
    res = oa.openai_chat("gpt-4o",gp.get_rpr_prompt(rp_setting,rp_history))
    text = []
    if res == None:
        text = ["営業ロープレを終了し、ゼロコンAIによる提案内容の評価を行います","申し訳ございません。エラーにより、評価結果が取得できませんでした"]
    else:
        text = ["営業ロープレを終了し、ゼロコンAIによる提案内容の評価を行います", "まず、今回の顧客の設定は以下の通りでした\n\n【顧客の設定】\n" + rp_setting, "次にゼロコンAIによる提案内容の評価は以下の通りでした\n\n【提案内容の評価】\n" + res]
    restart_text = ["もう一度同じ設定で営業ロープレを開始しますか？", "「はい」と返信すると会話をリセットし、同じ設定で再度営業ロープレを開始します(モード切替や「はい」以外の返信で終了します)"]
    text.append(restart_text)
    fa.reset_rp_history(db, user_data['userId'], isResetHistory=True, isRetryRP=True)
    return text

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
        current_index = plan_order.index(original_plan)
        if next_plan is None:
            next_index = 6
        else:
            next_index = plan_order.index(next_plan)
        desired_index = plan_order.index(desired_plan)

        if desired_plan == 'free':
            return 'free'
        elif (current_plan == 'free' or current_plan == '980') and desired_plan == 'try':
            return 'start_trial'
        elif desired_plan == 'try' and current_index > desired_index:
            return 'invalid_trial'
        elif desired_index == current_index:
            return 'already_subscribed'
        elif desired_plan == next_plan:
            return 'already_resv'
        elif next_plan != 'free' and current_index > next_index:
            return 'downgrade_resv'
        elif (original_plan == 'free' or original_plan == 'try') and desired_plan in ['980', '1980', '3980']:
            return 'new_subscription'
        elif current_index < desired_index:
            return 'upgrade'
        elif current_index > desired_index:
            return 'downgrade'
        else:
            return 'already_subscribed'
    
    def start_trial(self,action,desired_plan,isTrialValid):
        if isTrialValid:
            fa.set_pending_action(db, self.userId, {'action': action, 'desired_plan': desired_plan})
            return [f"【ご確認】\n3日間の無料トライアルを開始しますか？","※※※※※※※※※※※※※※※※※※※※※※\n\n・無料トライアル期間は3日間です\n\n・トライアル中は、中級プランと同様の機能がお使いいただけます\n\n・トライアル終了後は、もとのプランに戻ります\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください(「はい」以外の返信でキャンセルします)"]
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
            return [f"【ご契約内容の変更確認】\nご契約のプランを「{PLAN_NAMES[desired_plan]}」に変更します","※※※※※※※※※※※※※※※※※※※※※※\n\n・「はい」と返信いただくと、即時契約手続きが実行されます\n\n・本契約月から料金が発生します\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください(「はい」以外の返信でキャンセルします)"]

    def downgrade_sub(self,action,next_plan,desired_plan):
        if next_plan == 'free':
            return ['【ご連絡】\n解約予約されているため、プランの変更はできません\n\n解約完了後に再度ご契約ください']
        else:
            fa.set_pending_action(db, self.userId, {'action': action, 'desired_plan': desired_plan})
            return [f"【ご契約内容の変更予約の確認】\nご契約のプランを「{PLAN_NAMES[desired_plan]}」に変更予約します","※※※※※※※※※※※※※※※※※※※※※※\nプラン変更予約につき以下の点にご注意ください\n\n・本契約月は現在プランの料金が適用され、翌契約月から予約プランの料金が適用されます\n\n・プラン変更の完了まで、引き続き現在プランの機能をご利用可能です\n\n・プラン変更が完了するまで、他プランへの変更はできません\n\n※※※※※※※※※※※※※※※※※※※※※※","よろしければ「はい」と返信してください"]

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
        elif currentPlan == 'try' or currentPlan == '1980':
            return self.processMiddle(botType)
    
    def processBegin(self,botType):
        if botType == "fr":
            return ['メニューからモードを選択してください']
        elif botType == "kn":
            return self.res_kn()
        elif botType == "qa":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        elif botType == "yo":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        elif botType == "gs":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        elif botType == "rps":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        elif botType == "rpr":
            return ['本機能をご利用いただくには、中級以上のプランにご契約いただく必要があります']
        else:
            return ['エラー：無効なモードを指定しています']
    
    def processMiddle(self,botType):
        if botType == "fr":
            return ['メニューからモードを選択してください']
        elif botType == "kn":
            return self.res_kn()
        elif botType == "qa":
            return self.res_qa()
        elif botType == "yo":
            return self.res_yo()
        elif botType == "gs":
            return self.res_gs()
        elif botType == "rps" or botType == "rpr":
            return self.res_rp()
        else:
            return ['エラー：無効なモードを指定しています']

    def res_kn(self):
        query_type = self.norm_query_type(oa.openai_chat("gpt-4o-mini",gp.kn_class_prompt(self.userText)))
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
        cont  = self.norm_res_cont(oa.openai_chat("gpt-4o",gp.kl_response_prompt(query_type,self.userText)))
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
        res = self.norm_answer_cont(oa.openai_chat("gpt-4o",gp.get_qa_prompt(self.userText,qa_text)))
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
        searchTerms = self.norm_term_cont(oa.openai_chat("gpt-4o-mini",prompt))
        if not searchTerms:
            res = ["検索ワードの生成に失敗しました。再度、ご要望をお伝えください"]
            return res
        # youtube data api にて検索結果を表示
        result,textResult = ya.search_videos(searchTerms)
        if not result:
            res = ["YouTube動画検索に失敗しました。再度、ご要望をお伝えください"]
            return res
        
        # キューの内容に最も適切な検索結果を判断
        videoNum = self.norm_video_num(oa.openai_chat("gpt-4o-mini",gp.get_judg_prompt(self.userText, textResult)))
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
        print("convs:",convs)
        res = self.norm_gs_res(oa.openai_chat("gpt-4o",gp.get_gs_prompt(convs,self.userText)))
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
            text = f"""<content>
<speaker>{conv['speaker']}</speaker>
<massage>{conv['content']}</message>
</content>
"""
            text_list.append(text)
        return "".join(text_list)

    def norm_gs_res(self,text):
        pattern = r'<response>(.*?)</response>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def res_rp(self):
        if self.userData['isAlreadyRP']:
            return self._process_rp()
        else:
            return ["営業ロープレは終了しています。メニューから「開始＆リセット」をクリックして開始してください"]

    def _process_rp(self):
        rp_setting = self.userData['rp_setting']
        history_text = self.get_rphis_text(self.userData['rp_history'])
        print("history_text:",history_text)
        # res = self.norm_rp_res(oa.openai_chat("gpt-4o",gp.get_rp_prompt(rp_setting,history_text,self.userText)))
        res = oa.openai_chat("gpt-4o",gp.get_rp_prompt(rp_setting,history_text,self.userText))
        if res:
            # 会話履歴を更新
            fa.update_rp_history(db,self.userId,rp_data_limit,salesperson=self.userText,customer=res)
            return res
        else:
            return ["応答の取得に失敗しました。再度、テキストを送信してください"]
    
    def get_rphis_text(self,rp_history):
        text_list = []
        for conv in rp_history:
            text = f"""
<speaker>{conv['speaker']}</speaker>
<massage>{conv['content']}</message>
"""
            text_list.append(text)
        return "".join(text_list)
    
    # def norm_rp_res(self,text):
    #     pattern = r'<response>(.*?)</response>'
    #     match = re.search(pattern, text, re.DOTALL)
    #     if match:
    #         return match.group(1).strip()
    #     return None
    
# if __name__ == "__main__":
#     userText = "猫の動画を調べてください"
#     prompt = gp.get_searchYoutube_prompt(userText)
#     response = oa.openai_chat("gpt-4o-mini",prompt)
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
#     response = oa.openai_chat("gpt-4o-mini",prompt)
#     print("judgeResponse:",response)
#     videoNum = extract_video_numbers(response)
#     if not videoNum:
#         text = "YouTube動画検索に失敗しました。再度、ご要望をお伝えください"
#     response_text = gen_response_text(result,videoNum,searchTerms)
#     print("responseText:",response_text)


# プランアップグレードした際にpending_actionが適用されているせいで、モード切替後のテキストがはい/いいえ待ちになる
# 
# %%
