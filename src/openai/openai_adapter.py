import configparser
from dotenv import load_dotenv
from openai import OpenAI
import os
import logging

class OpenaiAdapter:

    load_dotenv()
    config = configparser.ConfigParser()
    config.read('config.ini')
    retry_limit = int(config.get('CONFIG', 'retry_limit', fallback=5))

    def __init__(self):
        self.client = OpenAI(
            api_key = os.getenv('OPENAI_API_KEY')
        )
        self.logger = logging.getLogger(__name__)

    def openai_chat(self, openai_model, prompt, temperature=0.7):
        """
        OpenAI APIを使用してチャット応答を生成します。

        Args:
            openai_model (str): 使用するモデル名
            prompt (str): プロンプト
            temperature (float, optional): 生成の多様性。デフォルトは1。

        Returns:
            str: 生成されたテキスト。エラー時はNone
        """
        system_prompt = [{"role": "system", "content": prompt}]
        for i in range(self.retry_limit):
            try:
                # Search-previewモデルの場合はtemperatureパラメータを除外
                params = {
                    "messages": system_prompt,
                    "model": openai_model,
                }
                if not openai_model.endswith("-search-preview"):
                    params["temperature"] = temperature

                response = self.client.chat.completions.create(**params)
                text = response.choices[0].message.content

                if text and text.strip():
                    self.logger.info(f"AIからの応答を受信: {text[:100]}...")
                    return text.strip()
                else:
                    self.logger.warning(f"AIからの応答が空でした (試行 {i + 1}/{self.retry_limit})")
                    if i == self.retry_limit - 1:
                        return None
                    continue

            except Exception as error:
                self.logger.error(f"GPT呼び出し時にエラーが発生: {str(error)} (試行 {i + 1}/{self.retry_limit})")
                if i == self.retry_limit - 1:
                    return None
                continue

    def embedding(self, texts):
        """
        テキストのベクトル表現を生成します。

        Args:
            texts (list): ベクトル表現を生成するテキストのリスト

        Returns:
            list: 生成されたベクトル表現のリスト。エラー時は空のリスト
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [d.embedding for d in response.data]
        except Exception as error:
            self.logger.error(f"埋め込みベクトル生成時にエラーが発生: {str(error)}")
            return []