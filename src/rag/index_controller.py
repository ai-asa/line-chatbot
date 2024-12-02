# %%
import configparser
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain.schema import Document
from src.openai.openai_adapter import OpenaiAdapter
from src.openai.get_prompt import GetPrompt
import os
import re
import pandas as pd

class IndexController:
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    config_file_path = 'config.ini'
    config = configparser.ConfigParser()
    config.read(config_file_path, encoding='utf-8')
    a_csv_path = config.get('INDEX', 'a_csv_path', fallback='./data/index/a.csv')
    q_index_path = config.get('INDEX','q_index_path', fallback='./data/index/')
    top_k = int(config.get('INDEX','top_k', fallback=3))
    openai_model = config.get('CONFIG', 'openai_model', fallback='gpt-4o-mini')
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY,model="text-embedding-3-large",deployment="text-embedding-3-large")
    oa = OpenaiAdapter()
    gp = GetPrompt()

    def __init__(self) -> None:
        # indexの読み込み
        try:
            self.q_index = FAISS.load_local(self.q_index_path, self.embeddings)
        except Exception as e:
            print(f"インデックスの読み込み中にエラーが発生したか、インデックスが存在しません。: {e}")
            self.q_index = None
        # a.csvの読み込み
        try:
            self.a_df = pd.read_csv(self.a_csv_path, encoding='utf-8-sig')
        except:
            print("作成済みのアンサードキュメントがありません。")
            self.a_df = pd.DataFrame()

# データ作成時
# csvファイルを取得して、dfに変換する
# Qテキストでインデックスを作成
## 作成時のメタデータに固有の識別番号を作成
## Qテキストに識別番号を割り振ったCSVファイルを作成する

    def create_index(self,q_text,a_text,a_cont,url,number) -> None:
        q_docs = [Document(page_content=q_text, metadata=dict(number=number,url=url))]
        if self.q_index:
            self.q_index.add_documents(q_docs)
        else:
            self.q_index = FAISS.from_documents(
                q_docs,
                self.embeddings,
                )
        a_text = a_text + "\n" + a_cont
        a_doc = pd.DataFrame({
                'number':[number],
                'a_text':[a_text]
                })
        self.a_df = pd.concat([self.a_df,a_doc])
        pass

    def save_index(self):
        try:
            self.a_df.to_csv(self.a_csv_path, encoding='utf-8-sig', index=False)
            print(f"CSVファイルが正常に保存されました: {self.a_csv_path}")
        except Exception as e:
            print(f"CSVファイルの保存中にエラーが発生しました: {e}")
        try:
            self.q_index.save_local(self.q_index_path)
            print(f"INDEXファイルが正常に保存されました: {self.q_index_path}")
        except Exception as e:
            print(f"INDEXファイルの保存中にエラーが発生しました: {e}")

# データ検索時
# Aテキストを取得してdfに変換する
# インデックスを読み込む
# クエリでインデックスを検索(L2距離)
# 検索結果の上位n件のメタデータから識別番号を取得
# 識別番号からAテキストを取得

    def search_index(self,query):
        # search Q text
        docs = self.q_index.similarity_search_with_score(query,k=self.top_k)
        # search A text
        qa_list = []
        qa_dict = {}
        i = 1
        for document in docs:
            q_text = document[0].page_content
            number = document[0].metadata['number']
            url = document[0].metadata['url']
            a_text = self.a_df[self.a_df['number'] == number].values[0][1]
            qa_list.append((i,q_text,a_text))
            qa_dict[i] = (q_text,a_text,url)
            i += 1
        return qa_list, qa_dict

# データの選択
# 取得したn個のQAテキストを1,2,...,nの数字とタプルにする
# openai apiにてどのQAテキストが今回のクエリと最も関係がありそうかを判断
# 選択されたQAテキストを返す

    def _extract_qa_number(self,text):
        pattern = r'<relevant_qa_number>\s*(\d+)'
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        else:
            return None

    def assist_ai(self,query,qa_list,qa_dict):
        prompt = self.gp.get_index_prompt(query,qa_list)
        print("prompt:",prompt)
        rs = self.oa.openai_chat(self.openai_model, prompt)
        print("rs:",rs)
        rs_num = self._extract_qa_number(rs)
        print("rs_num:",rs_num)
        if rs_num:
            return qa_dict[rs_num]
        else:
            return None, None

if __name__ == "__main__":
    ic = IndexControler()
    q_text = "question"
    a_text = "answer"
    lis_name = "ASA"
    query = "q"
    ic.create_index(lis_name,q_text,a_text,option="history")
    historys,summarys,old_historys,old_summarys = ic.search_lis_index(query,lis_name)

# %%
