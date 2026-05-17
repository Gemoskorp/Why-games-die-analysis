import requests
from bs4 import BeautifulSoup
from base_parser import BaseParser

class MetacriticParser(BaseParser):
    def __init__(self):
        super().__init__("data/raw/metacritic", delay=2.0)
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def parse_game(self, slug: str) -> dict:
        # slug это например "elden-ring", "the-witcher-3-wild-hunt"
        url = f"https://www.metacritic.com/game/{slug}/"
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, "html.parser")

        def get_score(selector):
            el = soup.select_one(selector)
            return el.text.strip() if el else None

        return {
            "slug":           slug,
            "metascore":      get_score(".c-productScoreInfo_scoreNumber"),
            "user_score":     get_score(".c-productScoreInfo_scoreNumber span"),
            "critic_reviews": get_score(".c-productScoreInfo_reviewsTotal"),
        }



if __name__ == "__main__":
    import pandas as pd
    import sys
    sys.path.append(".")
    
    game_names = pd.read_csv("data/game_ids.csv")["name"].tolist()
    print(f"Игр для парсинга: {len(game_names)}")
    
    parser = MetacriticParser()
    df = parser.parse_all(game_names)
    print(f"Готово! Спарсено: {len(df)}")
