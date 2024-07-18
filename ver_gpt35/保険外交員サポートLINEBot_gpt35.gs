// プロパティの取得
const props = PropertiesService.getScriptProperties();
const OPENAI_API_KEY = props.getProperty('OPENAI_API_KEY');

// プロンプトを取得
function get_response_prompt(variables) {
  let prompt = `<role_description>
あなたは日本の生命保険（損害保険を除く）と税法に関する深い理解を持つ、知識豊富な保険コンサルタントです。保険外交員をサポートする役割を担っており、以下の2つの状況に対応します：
1. 顧客に生命保険外交を行う際に必要な知識の提供
2. 顧客への効果的な生命保険提案方法のアドバイス
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
  4. 損害保険の質問の場合：
     - 損害保険については情報を持たないため答えてはいけません。
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
3. 保険税法：
   - 生命保険契約の税控除と確定申告での扱い
   - 相続税・贈与税に関する生命保険の活用戦略
4. カスタマイズされた推奨：
   - 年齢、性別、家族構成を考慮した保険推奨
   - 保障額の計算（日本の会計原則に基づく）
   - 変額保険、iDeCo、NISAの比較（iDeCoとNISAのデメリット強調）
5. 提案テクニック：
   - 顧客のニーズ分析方法
   - 効果的な説明と質問応対のテクニック
   - 異論対処法
   - 医療保険の必要性を説明する際の効果的なアプローチ
6. アポイントメントスクリプト：
   - 新規・既存顧客向けの状況に応じたスクリプト
   - LINEやメールでの依頼・変更スクリプト
</skills>

<constraints>
- 一般的な金融・生命保険情報のみを提供し、信頼性を維持してください。
- 違法または金融コンプライアンス規制に違反する可能性のある発言は避けてください。
- 医療保険の説明では、その必要性を治療費用や療養費用に関する具体的な情報を含めて説明してください。
- Markdown形式で出力してください
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
<response>
知識要求の場合：
1. 回答
[簡潔な回答の要約] 
2. 説明と関連情報
[詳細な説明と関連情報]
3. 例示など
[必要に応じた追加の文脈や例示]

提案方法相談の場合：
1. 提案の前提となる知識
[提案の前提となる知識の説明]
2. 提案シナリオ
[具体的な提案シナリオ] 
3. 提案セリフ
[具体的な提案セリフ] 
4. 想定質問と懸念事項への対処
[想定される質問や懸念事項への対処法]
</response>
</output_format>`;

  for (let key in variables) {
    prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), variables[key]);
  }
  return prompt;
}

function get_class_prompt(variables){
  let prompt = `<role_description>
あなたはユーザーの質問を分類する機械として振る舞います。
</role_description>

<user_query>
{user_query}
</user_query>

<user_query_identification>
ユーザーの質問を分析し、以下のいずれかに分類してください：
1. 知識要求：医療・生命保険、税法、市場動向などに関する事実情報を求める質問
2. 提案方法相談：顧客への保険提案や説明方法に関するアドバイスを求める質問
3. 保険商品名を含む質問：具体的な保険商品名を含む質問
4. 損害保険の質問：損害保険に関する質問
</user_query_identification>

<output_format>
[分類した番号の数字のみを出力してください]
</output_format>
`;
  for (let key in variables) {
    prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), variables[key]);
  }
  return prompt;
}

// OpenAI APIをコール
function callOpenAI(prompt, model = "gpt-3.5-turbo-0125") {
  try {
    const url = "https://api.openai.com/v1/chat/completions";
    const headers = {
      "Authorization": "Bearer " + OPENAI_API_KEY,
      "Content-Type": "application/json"
    };
    
    const payload = {
      model: model,
      messages: [{ role: "system", content: prompt }]
    };

    const options = {
      method: "post",
      headers: headers,
      payload: JSON.stringify(payload)
    };

    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());
    
    return result.choices[0].message.content;
  } catch (error) {
    logErrorToFile('Error in callOpenAI: ' + error.toString());
    return "申し訳ありません。現在システムに問題が発生しています。しばらくしてからもう一度お試しください。";
  }
}

// 実行関数
function doPost(e) {
  try {
    const json = JSON.parse(e.postData.contents);
    const events = json.events;
    events.forEach(function(event) {
      let replyToken = event.replyToken;
      let userId = event.source.userId;
      if (event.type == "message"){
        let userText = event.message.text;
        const variables = {
          user_query: userText
        }
        const class_prompt = get_class_prompt(variables);
        const query_type = processQueryType(callOpenAI(class_prompt));
        if (query_type == "3" || query_type == "4" || query_type == "5"){
          line_reply(userId, replyToken, query_type);
        } else {
          variables.query_type = query_type;
          const response_prompt = get_response_prompt(variables);
          const aiResponse = processResponse(callOpenAI(response_prompt));
          line_reply(userId, replyToken, query_type, aiResponse);
        }
      }
    });
    return ContentService.createTextOutput(JSON.stringify({status: 'success'})).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    logErrorToFile('Error in doPost: ' + error.toString());
    return ContentService.createTextOutput(JSON.stringify({status: 'error', message: error.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}

// LINEリプライ
function line_reply(userId, replyToken, queryType, replyText="" ) {
  if (queryType == "3") {
    replyText = "個別商品についてはお答えできません、直接お問い合わせください"
  } else if (queryType == "4") {
    replyText = "損害保険分野に関してはお答えできません"
  } else if (queryType == "5") {
    replyText = "質問内容の取得に失敗しました。再度質問してください。"
  }
  try {
    const response = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/reply', {
        'headers': {
            'Content-Type': 'application/json; charset=UTF-8',
            'Authorization': 'Bearer ' + props.getProperty('LINE_ACCESS_TOKEN'),
        },
        'method': 'post',
        'payload': JSON.stringify({
            'replyToken': replyToken,
            'messages': [{
                'type': 'text',
                'text': replyText,
            }]
        })
    });
  } catch (error) {
    logErrorToFile('Failed to send reply:', response.getContentText());
    line_push_notification(userId, replyText);  // プッシュ通知を送る
    logErrorToFile('Error in line_reply: ' + error.toString());
  }
}

// LINEプッシュ通知
function line_push_notification(userId, replyText) {
  try {
    const retryKey = Utilities.getUuid();  // UUIDを生成
    const response = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + props.getProperty('LINE_ACCESS_TOKEN'),
            'X-Line-Retry-Key': retryKey,
        },
        'method': 'post',
        'payload': JSON.stringify({
            'to': userId,
            'messages': [{
                'type': 'text',
                'text': replyText
            }]
        })
    });
  } catch (error) {
    logErrorToFile('Error in line_push_notification: ' + error.toString());
  }
}

// <response>タグをトリム
function processResponse(text) {
  const responseRegex = /<response>([\s\S]*?)<\/response>/;
  const match = text.match(responseRegex);
  
  if (match) {
    return match[1].trim();
  } else {
    return "質問内容の取得に失敗しました。再度質問してください。";
  }
}

// <query_type>タグ内の最初の数字を取得
function processQueryType(text) {
  const numberMatch = text.match(/\d+/);
  if (numberMatch) {
    return numberMatch[0];
  }
  return "5";
}

/**
 * エラーログをファイルに書き込む
 * @param {string} message - ログに書き込むメッセージ
 */
function logErrorToFile(message) {
  const scriptFile = DriveApp.getFileById(ScriptApp.getScriptId());
  const folders = scriptFile.getParents();
  if (folders.hasNext()) {
    const folder = folders.next();
    const timestamp = Utilities.formatDate(new Date(), "JST", "yyyy-MM-dd'T'HH:mm:ss'Z'");
    const fileName = timestamp + "_error_log.txt";
    folder.createFile(fileName, message);
  } else {
    console.error("Script file does not belong to any folder.");
  }
}