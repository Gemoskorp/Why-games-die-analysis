from playwright.sync_api import sync_playwright
from .base_parser import BaseParser
import json

class SteamDBParser(BaseParser):
    def __init__(self):
        super().__init__("data/raw/steamdb")

    def parse_game(self, game_id: int) -> dict:
        url = f"https://steamdb.info/app/{game_id}/charts/"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": "Mozilla/5.0"})
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # пик онлайна
            peak = page.query_selector(".peak-concurrent")
            peak_value = peak.inner_text().strip() if peak else None

            # история онлайна из таблицы
            rows = page.query_selector_all("table.table-condensed tbody tr")
            history = []
            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) >= 3:
                    history.append({
                        "month": cols[0].inner_text().strip(),
                        "avg_online": cols[1].inner_text().strip(),
                        "peak_online": cols[2].inner_text().strip(),
                    })

            browser.close()
            return {
                "steam_id": game_id,
                "peak_all_time": peak_value,
                "online_history": json.dumps(history),
            }

if __name__ == "__main__":
    import pandas as pd
    import sys
    sys.path.append(".")
    
    game_ids = pd.read_csv("data/game_ids.csv")["steam_id"].tolist()
    print(f"Игр для парсинга: {len(game_ids)}")
    
    parser = SteamDBParser()
    df = parser.parse_all(game_ids)
    print(f"Готово! Спарсено: {len(df)}")

