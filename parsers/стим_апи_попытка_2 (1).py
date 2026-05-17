import requests
import time
from base_parser import BaseParser

class SteamAPIParser(BaseParser):
    BASE_URL = "https://store.steampowered.com/api/appdetails"

    def __init__(self):
        super().__init__("data/raw/steam_api", delay=1.5)

    def parse_game(self, game_id: int) -> dict:
        # ключ не нужен — это публичный Store API
        r = requests.get(
            self.BASE_URL,
            params={"appids": game_id, "l": "english"},
            timeout=10
        ).json()

        data = r.get(str(game_id), {})
        if not data.get("success"):
            return {}

        d = data["data"]

        if d.get("type") != "game":
            return {}

        return {
            "steam_id":        game_id,
            "name":            d.get("name"),
            "release_date":    d.get("release_date", {}).get("date"),
            "developer":       ", ".join(d.get("developers", [])),
            "publisher":       ", ".join(d.get("publishers", [])),
            "price_usd":       d.get("price_overview", {}).get("final", 0) / 100,
            "is_free":         d.get("is_free", False),
            "genres":          ", ".join(g["description"] for g in d.get("genres", [])),
            "achievements":    d.get("achievements", {}).get("total", 0),
            "languages_count": len(d.get("supported_languages", "").split(",")),
        }