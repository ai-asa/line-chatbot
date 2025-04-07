import configparser

class GetPrompt:

   def __init__(self):
      config_file_path = 'config.ini'
      config = configparser.ConfigParser()
      config.read(config_file_path, encoding='utf-8')
      pass
    
   def get_index_prompt(self,query,qa_list):
      textList = []
      for qa in qa_list:
         number,q_text,a_text = qa
         text = f"""<{number}>
Q:{q_text}
A:{a_text}
</{number}>"""
         textList.append(text)
      t = "\n".join(textList)
      prompt = f"""あなたはユーザーの質問に基づいて、リストから最も関連性の高いQ&Aを選択するAIアシスタントです。Q&Aリストには生命保険、医療保障、税金に関する情報が含まれています。あなたの目標は、ユーザーの質問を分析し、それに最もマッチするQ&Aを選択することです。

まず、数字番号付きのQ&Aリストが提供されます：
<qa_list>
{t}
</qa_list>

次に、ユーザーの質問が提示されます：
<user_query>
{query}
</user_query>

最も関連性の高いQ&Aを選択するために、以下の手順に従ってください：
1. ユーザーの質問を注意深く読み、理解します。
2. 提供されたリストの各Q&Aを確認します。
3. 各Q&Aの内容とトピックをユーザーの質問と比較します。
4. 以下の点に基づいて各Q&Aの関連性を評価します： 
   a. トピックの類似性 
   b. 特定のキーワードやフレーズ 
   c. 質問の全体的な文脈
5. ユーザーの質問に最もマッチするQ&Aを選択します。

最も関連性の高いQ&Aを決定したら、以下の形式で出力してください：
<explanation>
[ここに選択理由の簡単な説明を記入してください。この説明では、あなたの選択につながる主要な要因を強調してください。]
</explanation>
<relevant_qa_number>
[ここに最も関連性の高いQ&Aの数字番号のみを記入]
</relevant_qa_number>

ユーザーの質問に基づいて最も関連性の高いQ&Aを選択することに専念してください。質問に直接回答したり、要求された以外の追加情報を提供したりしないでください。
"""
      return prompt

   def get_qa_prompt(self,query,qa_text):
      prompt = f"""あなたは生命保険、医療保障、税金等に関する質問に答える専門家AIアシスタントです。ユーザーからの質問に対して、正確で役立つ回答を提供することが目的です。
まず、QAを確認します。これには、よくある質問とその回答が含まれています：
<qa>
{qa_text}
</qa>

次にユーザーの質問を確認します。：
<user_question>
{query}
</user_question>

この質問に答えるために、以下の手順に従ってください：
1. QAとユーザーの質問に関連する情報を探してください。
2. 関連する情報が見つかった場合、それを基に回答を作成してください。複数の関連情報がある場合は、それらを組み合わせて包括的な回答を作成してください。
3. 関連する情報が見つからなかった場合、QAを参考にせず、関連するQAが見つからなかったことを報告します。
4. 回答を作成する際は、以下の点に注意してください：
   - 明確で簡潔な言葉を使用する
   - 専門用語がある場合は、可能な限り分かりやすく説明する
   - 必要に応じて、回答を複数の段落や箇条書きに分けて構造化する

作成した回答を以下の形式で記述してください：
<answer>
[ここに回答を記入]
</answer>

回答は正確かつ信頼性の高いものである必要があります。不確かな情報や推測は避け、提示されたQAとユーザーの質問に関連性が有る場合は、QAを基に回答を生成してください。ハルシネーションを起こさないでください。
"""
      return prompt

   def kn_class_prompt(self,user_query):
      prompt =f"""<role_description>
あなたはユーザーの質問を分類する機械として振る舞います。
</role_description>

<user_query>
{user_query}
</user_query>

<user_query_identification>
ユーザーの質問を分析し、以下のいずれかに分類してください：
1. 知識要求：生命,医療,損害保険、税法、市場動向などに関する事実情報を求める質問
2. 提案方法相談：顧客への保険提案や説明方法に関するアドバイスを求める質問
</user_query_identification>

<output_format>
[分類した番号の数字のみを出力してください]
</output_format>
"""
      return prompt

   def kl_response_prompt(self,query_type,user_query):
      prompt = f"""<role_description>
あなたは日本の生命,医療,損害保険と税法に関する深い理解を持つ、知識豊富な保険コンサルタントです。保険外交員をサポートする役割を担っており、以下の2つの状況に対応します：
1. 顧客に保険外交を行う際に必要な知識の提供
2. 顧客への効果的な保険提案方法のアドバイス
状況に応じて、適切な情報や提案を提供してください。特に、提案する際のセリフやトークの事例や仕方を教えてください。
</role_description>

<response_guidelines>
- 思いやりと理解のある口調を維持し、日本の文化的コンテキストを考慮してください。
- 質問のタイプに応じて、以下のように対応してください：
  1. 知識要求の場合：
     - 正確かつ最新の情報を提供してください。
     - 必要に応じて、複雑な概念を分かりやすく説明してください。
  2. 提案方法相談の場合：
     - 具体的な提案シナリオと提案時のセリフを提示してください。
     - 顧客の状況や心理を考慮したアプローチやセリフを推奨してください。
  3. 特定の保険商品名を含む質問
     - 個別の保険商品については正確な情報を持たないため答えてはいけません。
- 適用可能な場合は生命保険の利点を強調し、生命保険への加入を勧めるエビデンスを示してください
- ユーザー（保険外交員）の理解度に応じて言葉遣いや説明の深さを調整してください。
</response_guidelines>

<skills>
1. 生命保険知識：
   - 保険の種類（終身、定期、養老など）と主要会社の特徴
   - 日本特有の課題（終身雇用減少、高齢化）に対応する生命保険種類
2. 医療保険知識：
   - 治療費用、療養費用の具体的な数値や統計
   - 年齢や健康状態に応じた医療保険の必要性
3. 損害保険知識
   - 主要な損害保険の種類（火災保険、自動車保険、傷害保険など）とそれぞれの特徴
   - 日本の自然災害リスク（地震、台風、洪水など）に対応する特約や補償内容
4. 保険税法：
   - 保険契約の税控除と確定申告での扱い
   - 相続税・贈与税に関する生命保険の活用戦略
5. カスタマイズされた推奨：
   - 年齢、性別、家族構成を考慮した保険推奨
   - 保障額の計算（日本の会計原則に基づく）
   - 変額保険、iDeCo、NISAの比較（iDeCoとNISAのデメリット強調）
6. 提案テクニック：
   - 顧客のニーズ分析方法
   - 効果的な説明と質問応対のテクニック
   - 異論対処法
   - 保険の必要性を説明する際の効果的なアプローチ
7. アポイントメントスクリプト：
   - 新規・既存顧客向けの状況に応じたスクリプト
   - LINEやメールでの依頼・変更スクリプト
</skills>

<constraints>
- 一般的な金融・保険情報のみを提供し、信頼性を維持してください。
- 違法または金融コンプライアンス規制に違反する可能性のある発言は避けてください。
- 医療保険の説明では、その必要性を治療費用や療養費用に関する具体的な情報を含めて説明してください。
</constraints>

<user_query>
{user_query}
</user_query>

<user_query_identification>
ユーザーの質問は以下の2つに分類できます。
1. 知識要求：生命保険商品、税法、市場動向などに関する事実情報を求める質問
2. 提案方法相談：顧客への提案や説明方法に関するアドバイスを求める質問
今回の質問は{query_type}に分類されます。
</user_query_identification>

<output_format>
知識要求の場合：
<response>
1. 回答
[簡潔な回答の要約] 
2. 説明と関連情報
[詳細な説明と関連情報]
3. 例示など
[必要に応じた追加の文脈や例示]
</response>
提案方法相談の場合：
<response>
1. 提案の前提となる知識
[提案の前提となる知識の説明]
2. 提案シナリオ
[具体的な提案シナリオ] 
3. 提案セリフ
[具体的な提案セリフ] 
4. 想定質問と懸念事項への対処
[想定される質問や懸念事項への対処法]
</response>
</output_format>
"""
      return prompt
   
   def get_searchYoutube_prompt(self,user_query):
      prompt = f"""あなたはYouTubeで保険に関する動画を探すための最適な検索ワードを作成する専門家です。ユーザーの要求を満たす動画を検索するための最適な検索ワードを提案してください。

ユーザーのリクエストは以下の通りです：
<user_request>
{user_query}
</user_request>

検索ワードを作成する際は、以下の点に注意してください：
1. 簡潔で具体的な表現を使う
2. ユーザーのリクエストに関連するキーワードを使用する
3. 必要に応じて複数のキーワードを組み合わせる
4. ユーザーが言及した特定の要件や好みがあれば、それらを含める

出力は以下の点に注意してください：
1. 最初にユーザーのリクエストの内容を分析してください
   a. 主なトピック、要件、検索ワードに含めるべき重要な概念を特定してください
   b. リクエストの目的と要求される知見を特定してください
2. 検索ワードは単独、または複数のキーワードから構成してください
3. 検索ワードは複数の候補を提示し、多様な視点を確保してください

出力は以下の形式に従ってください：
<output>
<reasoning>
[ユーザーのリクエストの分析結果と、検索ワードの選定理由の説明]
</reasoning>
<search_terms1>
[1つ目の検索ワード。キーワードが複数ある場合は、スペースを空けて組み合わせてください]
</search_terms1>
<search_terms2>
[2つ目の検索ワード。キーワードが複数ある場合は、スペースを空けて組み合わせてください]
</search_terms2>
<search_terms3>
[3つ目の検索ワード。キーワードが複数ある場合は、スペースを空けて組み合わせてください]
</search_terms3>
</output>
"""
      return prompt

   def get_judg_prompt(self, user_query, search_result):
      prompt = f"""ユーザーのクエリに基づいて、検索結果のリストから最も適切なYouTube動画を選択してください。あなたの目標は、ユーザーの意図に最もマッチし、最も関連性の高い情報を提供するビデオを選ぶことです。

ユーザーのクエリは以下の通りです：
<user_query>
{user_query}
</user_query>

Youtubeの検索結果のリストは以下の通りです：
<youtube_results>
{search_result}
</youtube_results>

最も適切なビデオを選択するために、以下の手順に従ってください：
1. ユーザーのクエリを注意深く読み、その意図と情報ニーズを分析し理解します
2. 各YouTube検索結果を確認し、以下の点に注意を払います：
   - ビデオのタイトル
   - ビデオの説明
   - チャンネル名
   - 高評価数
   - 視聴回数
   - アップロード日
3. 各ビデオを評価する際に、以下の要素を考慮します：
   - ユーザーのクエリとの関連性
   - チャンネルの信頼性
   - 情報の新しさ
   - 人気度（視聴回数、高評価数）
   - 説明に基づくコンテンツの包括性

出力は以下のように制御してください：
1. ユーザーのクエリの意図や情報ニーズを分析し動画選択の理由を説明してください
2. 適切な動画を3つまで選択し、番号を出力してください

出力は以下の形式に従ってください：
<output>
<reasoning>
[ユーザークエリの分析と、各ビデオを選んだ理由の説明]
</reasoning>
<first_selected_video>
[選択したビデオの番号]
</first_selected_video>
<second_selected_video>
[選択したビデオの番号]
</second_selected_video>
<third_selected_video>
[選択したビデオの番号]
</third_selected_video>
</output>

必ずユーザーのクエリとYouTube検索結果に提供された情報のみに基づいて決定を下してください。与えられたデータに存在しない外部の知識や仮定を使用しないでください。
"""
      return prompt

   def get_gs_prompt(self,convs,user_input):
      prompt = f"""あなたは会話を通じて保険営業員を総合的にサポートするために設計されたAIアシスタントです。あなたの役割は、保険営業員の疑問や悩みに対して、その意図や抽象的な懸念を明確にし、保険知識や営業テクニックについてアドバイスを提供することです。以下のガイドラインに従って対応してください：

1. まずは営業員の状況や疑問を明確にするクリティカルな質問をすること
2. 保険の一般的な知識や営業アドバイスを提供するが、ハルシネーションに注意すること
3. これまでの営業員とAIアシスタントの会話を自然に続けること
4. 必要に応じて営業員のメンタルサポートを行うこと。その際、質問攻めはしないこと

異なる種類のサポート方法：
- 保険知識に関する疑問について：
  保険に関する一般的で事実に基づいた情報を提供。具体的な詳細が不確かな場合は、その限界を認め、公式リソースの参照を提案する。
- 営業テクニックに関する問題について：
  状況を明確にする質問をしてから、適切な営業戦略についてアドバイスを提供する。
- 営業への不安やモチベーション不足について：
  友人のように寄り添い、同調したり状況を質問する。質問攻めや、説教にならないようにアドバイスを送る

営業員とAIアシスタントのこれまでの会話は以下のとおりです：
<conversations>
{convs}
</conversations>

営業員の入力は以下のとおりです：
<user_input>
{user_input}
</user_input>

入力を分析し、以下の構造で回答を出力してください：
<assistant_output>
<understanding>
営業員の入力の意図の明確化と、必要なサポートの種類を整理
</understanding>
<response>
営業員に伝える文章
</response>
</assistant_output>

注意事項：
- まずは営業員の状況や疑問を明確にするクリティカルな質問をすること。ただし、質問攻めにはしないこと
- 具体的な保険商品の詳細や価格は提供しないこと
- 不確かな情報について質問された場合は、その限界を認め、公式ソースの参照を提案すること
- 適切に改行してください
"""
      return prompt
   
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

営業員とAIアシスタントのこれまでの会話：
<history>{history_text}
</history>

現在の営業員の発言：
<current_comment>
{user_input}
</current_comment>

応答の注意事項：
- 適切に改行してください
- 自ら会話を振らず、あくまで営業員の発言に応答してください
- 返答は簡潔にし、質問があるとき以外は1文程度の短い文章で応答してください

営業員の発言に対し、応答してください："""
      return prompt
   
   def get_rpr_prompt(self,rp_setting, history_text):
      prompt = f"""あなたは保険営業の会話分析の専門AIです。以下の会話記録をもとに、営業員の提案が適切に行われているかを評価してください。

入力情報：
<input_info>
1. 顧客情報：
<customer_info>
{rp_setting}
</customer_info>

2. 会話記録：
<conversation_record>
{history_text}
</conversation_record>
</input_info>

評価のフェーズと観点：
<evaluation_points>
1. **プリアプローチ:**  
   - 自然な挨拶や自己紹介から保険の話題にスムーズにつなげられているか。
2. **アプローチ:**  
   - 顧客の生活状況や背景、ニーズが十分にヒアリングされているか。特にこの段階のヒアリングが不足している場合、後の提案の根拠が弱くなる可能性がある。
3. **ファクトファインディング:**  
   - 顧客の心配事、リスク要因、生活上の不安や問題が明確に引き出され、その情報が保険提案に適切につながっているか。
4. **プレゼンテーション:**  
   - 提案中に顧客の反応（疑問、不安、関心など）を的確に把握し、提案内容の調整が行われているか。
5. **クロージング:**  
   - 顧客が最終的に決断に至るための説得力があり、前段階の聞き漏らしやミスがなくスムーズに決断が促されているか。
</evaluation_points>

その他チェックポイント：
<other_checkpoints>
- リスク説明が過剰でないか、また保険のデメリットや税務関連の説明が過剰に話されていないか、整合性やバランスが取れているかも評価してください。
- 顧客の個別情報（例：家族構成、居住地、保険加入状況など）を踏まえた適切なアプローチができているか。
- 各フェーズ間での情報の一貫性や論理的な流れがあるかも確認すること。
</other_checkpoints>

出力フォーマット：
<output_format>
- 各フェーズごとに「良かった点」と「改善点」を箇条書きで示してください。
- 全体の総評として、会話の流れや提案の整合性についても簡潔にまとめてください。
</output_format>

上記の基準に従い、入力された会話記録を分析し、営業員の保険提案に対する批評とフィードバックを出力してください。
"""
      return prompt

   def get_insurance_search_prompt(self, insurance_info):
      prompt = f"""あなたは保険会社と保険商品の正式名称を調査するAIアシスタントです。
ユーザーから提供された情報を元に、保険会社と保険商品の正式名称を特定してください。

ユーザーから提供された情報：
<insurance_info>
{insurance_info}
</insurance_info>

以下の点に注意して調査を行ってください：
1. 保険会社名と保険商品名の正式名称を特定する
2. 略称や通称が使用されている場合は、正式名称に変換する
3. 該当する保険会社、保険商品名がない場合は、それぞれNoneとする

出力は以下の形式で行ってください：
<result>
<company_name>
[保険会社の正式名称、ない場合はNone]
</company_name>
<product_name>
[保険商品の正式名称、ない場合はNone]
</product_name>
</result>"""
      return prompt

   def get_insurance_verification_prompt(self, search_results, target_insurance):
      prompt = f"""あなたは保険商品の照合を行うAIアシスタントです。提供された検索結果から、対象の保険商品と一致するものを特定してください。

検索結果の保険商品リスト：
<search_results>
{search_results}
</search_results>

対象の保険商品：
<target_insurance>
{target_insurance}
</target_insurance>

以下の基準で判断してください：
1. 保険会社名と商品名が完全に一致する場合、その番号を出力
2. 一致する商品が見つからない場合は、Noneを出力

出力形式：
<result_number>
[一致した保険商品の番号、または None]
</result_number>"""
      return prompt
   
   def get_insurance_product_search_details_prompt(self):
      """
      保険商品の詳細情報を収集するためのプロンプト
      
      Returns:
         str: 保険商品詳細検索用プロンプト
      """
      return """あなたは保険商品の調査専門家です。
   指定された生命保険商品について、ウェブ上の情報を徹底的に調査・収集し、詳細な情報をまとめてください。

   調査項目：
   1. 商品の基本情報
      - 正式名称と愛称
      - 販売開始時期
      - 主な特徴や特色
      - 対象年齢や加入条件

   2. 保障内容
      - 主な保障内容と保障額
      - 特約の種類と内容
      - 保険期間や保険料払込期間
      - 給付金や保険金の種類と支払条件

   3. 商品の特徴
      - 他社商品との差別化ポイント
      - 独自の保障や特約
      - 最新の改定内容（該当する場合）
      - 受賞歴や評価（該当する場合）

   4. 想定される顧客層
      - 主なターゲット層
      - 推奨される加入時期や状況
      - 顧客のニーズとの適合性

   5. 保険料に関する情報
      - 保険料の目安
      - 保険料に影響する要因
      - 割引制度の有無

   出力形式：
   <product_details>
   # 商品の基本情報
   - 正式名称：{商品の正式名称}
   - 愛称：{商品の愛称（ある場合）}
   - 販売開始時期：{販売開始時期}
   - 対象年齢：{対象年齢範囲}
   - 加入条件：{主な加入条件}

   # 保障内容
   - 主な保障内容：{主な保障内容の説明}
   - 保障額：{保障額の範囲や条件}
   - 特約：{特約の種類と内容}
   - 保険期間：{保険期間や保険料払込期間}
   - 給付金・保険金：{給付金や保険金の種類と支払条件}

   # 商品の特徴
   - 差別化ポイント：{他社商品との差別化ポイント}
   - 独自の保障：{独自の保障や特約の説明}
   - 最新の改定：{最新の改定内容（該当する場合）}
   - 受賞歴・評価：{受賞歴や評価（該当する場合）}

   # 想定される顧客層
   - ターゲット層：{主なターゲット層の説明}
   - 推奨加入時期：{推奨される加入時期や状況}
   - ニーズとの適合性：{顧客のニーズとの適合性}

   # 保険料情報
   - 保険料の目安：{保険料の目安}
   - 影響要因：{保険料に影響する要因}
   - 割引制度：{割引制度の有無と内容}

   # 情報源
   {情報源のURL1}
   {情報源のURL2}
   </product_details>

   注意事項：
   - 必ず複数の情報源を確認し、信頼性の高い情報のみを収集してください
   - 情報の出典は必ず記録してください
   - 情報が見つからない項目は「情報なし」と記載してください
   - 推測や憶測は避け、確実な情報のみを記載してください
   - 最新の情報であることを確認してください

   以下の生命保険商品について、ウェブ上の情報を徹底的に調査し、
   詳細情報を収集してください："""

   def get_insurance_summary_prompt(self,company: str, product_name: str, content: str) -> str:
      """
      保険商品の概要を生成するためのプロンプトを作成します。

      Args:
         company (str): 保険会社名
         product_name (str): 商品名
         content (str): 商品の詳細内容

      Returns:
         str: プロンプトテキスト
      """
      return f"""あなたは保険商品の概要を作成する専門家です。
   以下の保険商品について、簡潔で分かりやすい概要を作成してください。

   保険会社: {company}
   商品名: {product_name}
   商品内容:
   {content}

   作成基準：
   1. 保険会社名と商品名を含めて記載
   2. 保険の種類（生命保険、医療保険、がん保険など）を明記
   3. 主な特徴と内容を端的に示した説明（100文字程度）

   出力形式：
   <insurance_summary>
   [保険会社名]の[商品名]は、[保険の種類]です。[主な特徴と内容の説明]
   </insurance_summary>

   注意事項：
   - 必ず保険会社名と商品名を含めてください
   - 保険の種類を明確に示してください
   - 説明は簡潔かつ具体的にしてください
   - 箇条書きは使用せず、一つの文章にまとめてください
   - 出力は1段落のみとしてください"""

   def get_insurance_proposal_prompt(self, insured_info, current_insurance, target_insurance):
      """
      保険商品の乗り換え提案を生成するためのプロンプト
      
      Args:
         insured_info (dict): 被保険者の情報
         current_insurance (dict): 現在の保険商品情報
         target_insurance (dict): 乗り換え先の保険商品情報
         
      Returns:
         str: 乗り換え提案生成用プロンプト
      """
      prompt = f"""あなたは保険商品の乗り換え提案を作成する専門家です。
以下の情報を基に、保険商品の乗り換え提案を作成してください。

【被保険者情報】
{insured_info['info']}

【現在の保険商品】
■ 保険会社：{current_insurance['company']}
■ 商品名：{current_insurance['insurance_name']}
■ 保険料：{current_insurance.get('premium', 'N/A')}
■ 商品詳細：
{current_insurance['content']}

【乗り換え先の保険商品】
■ 保険会社：{target_insurance['company']}
■ 商品名：{target_insurance['insurance_name']}
■ 保険料：{target_insurance.get('premium', 'N/A')}
■ 商品詳細：
{target_insurance['content']}

以下の要素を含めた乗り換え提案を作成してください：

1. 両商品の特徴解説
- 現在加入中の保険商品の主な特徴
- 乗り換え先保険商品の主な特徴
- 両者の保障内容の違い
- 保険料水準の比較

2. メリット・デメリット分析
- 現在の保険商品のメリット・デメリット
- 乗り換え先商品のメリット・デメリット
- 保障内容の比較における優位点・懸念点
- 保険料に関する比較分析

3. 両商品評価（100点満点）
- 保障内容の充実度
- 保険料の経済性
- 特約や付加サービスの充実度
- 保険会社の信頼性・安定性
- 商品性の将来性

4. 乗り換え提案の方法論
- 具体的な提案の流れ
- 説明時の注意点
- 想定される顧客の状況を2,3個
- 対する提案論法とセリフ例

5. 総評と反論対応
- 乗り換えの総合的な判断
- 想定される顧客からの質問や反論を2,3個
- 対する保険情報を基にした具体的な返答例
- 乗り換えに関する注意点の説明

出力形式：
<feature_analysis>
[両商品の特徴解説]
</feature_analysis>

<merit_demerits>
[両商品のメリット・デメリット分析]
</merit_demerits>

<evaluation_score>
[両商品評価（100点満点）]
</evaluation_score>

<proposal_method>
[乗り換え提案の方法論]
</proposal_method>

<overall_evaluation>
[総評と反論対応]
</overall_evaluation>

注意事項：
- 客観的な事実に基づいて提案を作成すること
- 誇張や虚偽の情報を含まないこと
- 顧客の利益を最優先に考えること
- コンプライアンスに配慮すること
- 各セクションは必ず対応するタグで囲むこと
- 説明は体系的に整理して記述すること
- 太字は""で囲み、箇条書きは・を使用すること
"""
      return prompt

   def get_insurance_content_verification_prompt(self, content: str) -> str:
      """
      保険商品の内容が十分な情報を含んでいるかを判定するためのプロンプト
      
      Args:
          content (str): 評価する保険商品の内容
          
      Returns:
          str: 判定用のプロンプト
      """
      prompt = f"""あなたは保険商品の情報を評価する専門家AIです。
提供された保険商品の内容を評価し、十分な情報が含まれているかを判定してください。

評価する内容:
{content}

判定基準:
1. 保険商品の主な特徴が説明されているか
2. 保障内容が具体的に記載されているか
3. 商品の目的や対象者が明確か
4. 保険料や保険金に関する基本的な情報が含まれているか
5. 重要な特約や条件が説明されているか

以下の場合はfalseと判定してください：
- 内容が空の場合
- 内容が不明確または曖昧な場合
- 上記の判定基準の3つ以上が満たされていない場合
- 内容が明らかに不十分な場合

回答は true または false のみで返してください。
"""
      return prompt