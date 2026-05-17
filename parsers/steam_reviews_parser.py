import requests
from base_parser import BaseParser

class SteamReviewsParser(BaseParser):
    def __init__(self):
        super().__init__("data/raw/steam_reviews", delay=1.5)

    def parse_game(self, game_id: int) -> dict:
        url = f"https://store.steampowered.com/appreviews/{game_id}"
        params = {
            "json": 1,
            "language": "all",
            "review_type": "all",
            "purchase_type": "all",
            "num_per_page": 0,  # нужна только сводка, не сами отзывы
        }
        r = requests.get(url, params=params).json()
        summary = r.get("query_summary", {})

        total = summary.get("total_reviews", 0)
        positive = summary.get("total_positive", 0)

        return {
            "steam_id":          game_id,
            "total_reviews":     total,
            "total_positive":    positive,
            "total_negative":    summary.get("total_negative", 0),
            "positive_ratio":    round(positive / max(total, 1), 3),
            "review_score_desc": summary.get("review_score_desc", ""),
        }



if __name__ == "__main__":
    import pandas as pd
    import sys
    sys.path.append(".")
    
    game_ids = pd.read_csv("data/game_ids.csv")["steam_id"].tolist()
    print(f"Игр для парсинга: {len(game_ids)}")
    
    parser = SteamReviewsParser()
    df = parser.parse_all(game_ids)
    print(f"Готово! Спарсено: {len(df)}")



