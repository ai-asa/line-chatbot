# %%
import pandas as pd
import configparser
from src.rag.index_controller import IndexControler

config_file_path = 'config.txt'
config = configparser.ConfigParser()
config.read(config_file_path, encoding='utf-8')
qa_csv_path = config.get('INDEX', 'qa_csv_path', fallback='./data/qa/qa.csv')
# qa.csvの読み込み
try:
    qa_df = pd.read_csv(qa_csv_path, encoding='utf-8-sig')
except:
    print("qa.csvが見つかりません。")
    qa_df = pd.DataFrame()
pass

if __name__ == "__main__":
    ic = IndexControler()
    if not qa_df.empty:
        i=1
        for index, row in qa_df.iterrows():
            ic.create_index(row["Q"],row["A"],row["内容"],row["url"],i)
            i += 1
        ic.save_index()
    """
    query = "保険料はどのように決まりますか？今、保険の契約を行おうとしていますが、より多くの保険料をもらうためにどうしたらいいかを考えています。"
    qa_list, qa_dict = ic.search_index(query)
    q, a = ic.assist_ai(query,qa_list,qa_dict)
    print("q:",q)
    print("a:",a)
    """

# %%
