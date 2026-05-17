import requests
from base_parser import BaseParser

class HLTBParser(BaseParser):
    def init(self):
        super().init("data/raw/hltb", delay=2.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://howlongtobeat.com",
            "Origin":     "https://howlongtobeat.com",
        }

    def parse_game(self, game_name: str) -> dict:
        # сначала получаем актуальный ключ поиска со страницы
        search_key = self._get_search_key()
        if not search_key:
            return {"name": game_name}

        url = f"https://howlongtobeat.com/api/search/{search_key}"
        payload = {
            "searchTerms": game_name.split(),
            "searchPage":  1,
            "size":        1,
            "searchOptions": {
                "games": {
                    "userId": 0,
                    "platform": "",
                    "sortCategory": "popular",
                    "rangeCategory": "main",
                    "rangeTime": {"min": None, "max": None},
                    "gameplay": {"perspective": "", "flow": "", "genre": ""},
                    "rangeYear": {"min": "", "max": ""},
                    "modifier": "",
                },
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0,
            },
        }

        r = requests.post(url, json=payload, headers=self.headers)
        data = r.json().get("data", [])

        if not data:
            return {"name": game_name}

        g = data[0]
        return {
            "name":          game_name,
            "hltb_main":     round(g.get("comp_main", 0) / 3600, 1),     # секунды → часы
            "hltb_extra":    round(g.get("comp_plus", 0) / 3600, 1),
            "hltb_complete": round(g.get("comp_100", 0) / 3600, 1),
            "hltb_reviews":  g.get("review_score", 0),
        }

    def _get_search_key(self) -> str:
        # HLTB периодически меняет ключ в JS — берём актуальный
        try:
            r = requests.get("https://howlongtobeat.com", headers=self.headers)
            # ищем ключ вида /api/search/abcd1234
            import re
            match = re.search(r'"/api/search/(\w+)"', r.text)
            return match.group(1) if match else None
        except:
            return None
            
if name == "main":
    import pandas as pd
    import sys
    sys.path.append(".")
    
    game_names = pd.read_csv("data/game_ids.csv")["name"].tolist()
    print(f"Игр для парсинга: {len(game_names)}")
    
    parser = HLTBParser()
    df = parser.parse_all(game_names)
    print(f"Готово! Спарсено: {len(df)}")
