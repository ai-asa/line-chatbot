# %%
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from typing import List, Dict
from datetime import datetime

class YoutubeDataApiAdapter:

    # YouTube APIクライアントを構築
    youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_DATA_API_KEY"))

    def __init__(self):
        pass

    def search_videos(self, queries: List[str], max_results: int = 10, min_view_count: int = 0) -> List[Dict]:
        all_videos = []
        seen_video_ids = set()

        for query in queries:
            try:
                # 検索リクエストを実行
                search_response = self.youtube.search().list(
                    q=query,
                    type="video",
                    part="id,snippet",
                    maxResults=max_results,
                    # order="viewCount"  # 再生数順にソート
                ).execute()

                # 結果を処理
                for search_result in search_response.get("items", []):
                    video_id = search_result["id"]["videoId"]
                    
                    # 重複チェック
                    if video_id in seen_video_ids:
                        continue
                    
                    # 動画の詳細情報を取得
                    video_response = self.youtube.videos().list(
                        part="statistics",
                        id=video_id
                    ).execute()
                    
                    # 統計情報を取得
                    statistics = video_response["items"][0]["statistics"]
                    view_count = int(statistics.get("viewCount", 0))
                    
                    # 最小再生数でフィルタリング
                    if view_count < min_view_count:
                        continue

                    seen_video_ids.add(video_id)
                    published_at = datetime.strptime(search_result["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
                    
                    video = {
                        "title": search_result["snippet"]["title"],
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "description": search_result["snippet"]["description"],
                        "view_count": view_count,
                        "like_count": int(statistics.get("likeCount", 0)),
                        "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "search_query": query
                    }
                    all_videos.append(video)

            except HttpError as e:
                print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
                return None,None

        # 結果をビュー数で降順ソート
        all_videos.sort(key=lambda x: x['view_count'], reverse=True)

        # 結果を max_results に制限
        all_videos = all_videos[:max_results]

        # 結果に番号を付ける
        for num, video in enumerate(all_videos, 1):
            video['num'] = num

        # テキスト形式の結果を生成
        text_result = ""
        for video in all_videos:
            text_result += f"{video['num']}. {video['title']}\n"
            text_result += f"   Description: {video['description'][:50]}...\n"
            text_result += f"   Views: {video['view_count']}\n"
            text_result += f"   Likes: {video['like_count']}\n"
            text_result += f"   Published: {video['published_at']}\n\n"

        return all_videos, text_result

# 使用例
if __name__ == "__main__":
    ya = YoutubeDataApiAdapter()
    search_queries = ["猫の生態", "犬の生態", "ペットの飼い方"]
    results, text_output = ya.search_videos(search_queries, max_results=10, min_view_count=10000)
    
    if results:
        print("Structured results:")
        for video in results:
            print(f"{video['num']}. {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   Description: {video['description'][:50]}...")
            print(f"   Views: {video['view_count']}")
            print(f"   Likes: {video['like_count']}")
            print(f"   Search Query: {video['search_query']}")
            print()
        
        print("\nText output:")
        print(text_output)
    else:
        print("No results found or an error occurred.")
# %%
