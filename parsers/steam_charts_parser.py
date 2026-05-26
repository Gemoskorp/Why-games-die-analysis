import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import sys
from base_parser import BaseParser


class SteamChartsParser(BaseParser):
    def __init__(self):
        super().__init__("data/raw/steamcharts", delay=2.0)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _is_dead_by_history(self, peak_all_time: int, history: list) -> bool | None:
        if not history or not peak_all_time or peak_all_time == 0:
            return None

        threshold = peak_all_time / 10
        months = [h for h in history if h["month"] != "Last 30 Days"]

        if len(months) < 36:
            return None

        last_36 = months[:36]
        for m in last_36:
            try:
                avg = float(m["avg_players"])
                if avg >= threshold:
                    return False
            except:
                continue

        return True

    def _is_dead_by_current(self, game_id: int) -> bool | None:
        url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        try:
            r = self.session.get(url, params={"appid": game_id}, timeout=10)
            r.raise_for_status()
            data = r.json()
            player_count = data.get("response", {}).get("player_count")
            if player_count is None:
                return None
            return player_count < 5
        except:
            return None

    def _parse_steamcharts(self, game_id: int) -> dict | None:
        url = f"https://steamcharts.com/app/{game_id}"
        try:
            r = self.session.get(url, timeout=15)
        except:
            return None

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        peak_all_time = None
        peak_24h = None

        for stat in soup.select(".app-stat"):
            label = stat.get_text()
            num = stat.select_one(".num")
            if not num:
                continue
            value = num.text.strip().replace(",", "")
            if "all-time" in label:
                try:
                    peak_all_time = int(value)
                except:
                    pass
            elif "24-hour" in label:
                try:
                    peak_24h = int(value)
                except:
                    pass

        history = []
        table = soup.select_one("table.common-table tbody")
        if table:
            for row in table.select("tr"):
                cols = row.select("td")
                if len(cols) >= 5:
                    history.append({
                        "month":       cols[0].text.strip(),
                        "avg_players": cols[1].text.strip().replace(",", ""),
                        "gain":        cols[2].text.strip(),
                        "gain_pct":    cols[3].text.strip(),
                        "peak":        cols[4].text.strip().replace(",", ""),
                    })

        return {
            "peak_all_time": peak_all_time,
            "peak_24h":      peak_24h,
            "history":       history,
        }

    def parse_game(self, game: dict) -> dict | None:
        game_id   = game["steam_id"]
        game_name = game["name"]

        # шаг 1 — пробуем SteamCharts
        sc = self._parse_steamcharts(game_id)

        if sc:
            is_dead = self._is_dead_by_history(sc["peak_all_time"], sc["history"])
            source = "steamcharts"
        else:
            is_dead = None
            source = None

        # шаг 2 — если SteamCharts не дал ответа, используем Steam API
        if is_dead is None:
            is_dead = self._is_dead_by_current(game_id)
            source = "steam_api" if is_dead is not None else None

        print(
            f"  {game_name} | "
            f"peak={sc['peak_all_time'] if sc else None} | "
            f"dead={is_dead} | "
            f"source={source}"
        )

        return {
            "steam_id":      game_id,
            "name":          game_name,
            "peak_all_time": sc["peak_all_time"] if sc else None,
            "peak_24h":      sc["peak_24h"]      if sc else None,
            "is_dead":       is_dead,
            "dead_source":   source,
            "history":       json.dumps(sc["history"]) if sc else None,
        }


if __name__ == "__main__":
    sys.path.append(".")

    df_games = pd.read_csv("data/game_ids.csv")[["steam_id", "name"]]
    games = df_games.to_dict("records")
    print(f"Игр для парсинга: {len(games)}")

    parser = SteamChartsParser()
    df = parser.parse_all(games)

    print(f"\nГотово! Всего: {len(df)}")
    print(f"Мёртвых:    {len(df[df['is_dead'] == True])}")
    print(f"Живых:      {len(df[df['is_dead'] == False])}")
    print(f"Нет данных: {len(df[df['is_dead'].isna()])}")
    print(df[["steam_id", "name", "peak_all_time", "is_dead", "dead_source"]])














# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import json
# import sys
# from base_parser import BaseParser


# class SteamChartsParser(BaseParser):
#     def __init__(self):
#         super().__init__("data/raw/steamcharts", delay=2.0)
#         self.session = requests.Session()
#         self.session.headers.update({
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         })

#     def _is_dead(self, peak_all_time: int, history: list) -> bool | None:
#         if not history or not peak_all_time or peak_all_time == 0:
#             return None

#         threshold = peak_all_time / 10

#         months = [h for h in history if h["month"] != "Last 30 Days"]

#         if len(months) < 36:
#             return None

#         last_36 = months[:36]

#         for m in last_36:
#             try:
#                 avg = float(m["avg_players"])
#                 if avg >= threshold:
#                     return False
#             except:
#                 continue

#         return True

#     def parse_game(self, game: dict) -> dict | None:
#         game_id = game["steam_id"]
#         game_name = game["name"]
#         url = f"https://steamcharts.com/app/{game_id}"

#         try:
#             r = self.session.get(url, timeout=15)
#         except Exception as e:
#             print(f"  Ошибка сети: {e}")
#             return None

#         if r.status_code != 200:
#             print(f"  Статус {r.status_code}: {game_name}")
#             return None

#         soup = BeautifulSoup(r.text, "html.parser")

#         peak_all_time = None
#         peak_24h = None

#         for stat in soup.select(".app-stat"):
#             label = stat.get_text()
#             num = stat.select_one(".num")
#             if not num:
#                 continue
#             value = num.text.strip().replace(",", "")
#             if "all-time" in label:
#                 try:
#                     peak_all_time = int(value)
#                 except:
#                     pass
#             elif "24-hour" in label:
#                 try:
#                     peak_24h = int(value)
#                 except:
#                     pass

#         history = []
#         table = soup.select_one("table.common-table tbody")
#         if table:
#             for row in table.select("tr"):
#                 cols = row.select("td")
#                 if len(cols) >= 5:
#                     history.append({
#                         "month":       cols[0].text.strip(),
#                         "avg_players": cols[1].text.strip().replace(",", ""),
#                         "gain":        cols[2].text.strip(),
#                         "gain_pct":    cols[3].text.strip(),
#                         "peak":        cols[4].text.strip().replace(",", ""),
#                     })

#         is_dead = self._is_dead(peak_all_time, history)

#         print(
#             f"  {game_name} | peak_all={peak_all_time} | "
#             f"peak_24h={peak_24h} | "
#             f"months={len(history)} | "
#             f"dead={is_dead}"
#         )

#         return {
#             "steam_id":      game_id,
#             "name":          game_name,
#             "peak_all_time": peak_all_time,
#             "peak_24h":      peak_24h,
#             "is_dead":       is_dead,
#             "history":       json.dumps(history),
#         }


# if __name__ == "__main__":
#     sys.path.append(".")

#     df_games = pd.read_csv("data/game_ids.csv")[["steam_id", "name"]]
#     games = df_games.to_dict("records")
#     print(f"Игр для парсинга: {len(games)}")

#     parser = SteamChartsParser()
#     df = parser.parse_all(games)

#     print(f"\nГотово! Всего: {len(df)}")
#     print(f"Мёртвых:    {len(df[df['is_dead'] == True])}")
#     print(f"Живых:      {len(df[df['is_dead'] == False])}")
#     print(f"Нет данных: {len(df[df['is_dead'].isna()])}")
#     print(df[["steam_id", "name", "peak_all_time", "peak_24h", "is_dead"]])