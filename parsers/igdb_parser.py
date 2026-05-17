import requests
from base_parser import BaseParser

class IGDBParser(BaseParser):
    def init(self, client_id: str, client_secret: str):
        super().init("data/raw/igdb", delay=0.3)
        self.client_id = client_id
        self.access_token = self._get_token(client_secret)

    def _get_token(self, client_secret: str) -> str:
        r = requests.post("https://id.twitch.tv/oauth2/token", params={
            "client_id":     self.client_id,
            "client_secret": client_secret,
            "grant_type":    "client_credentials",
        })
        return r.json()["access_token"]

    def parse_game(self, game_name: str) -> dict:
        headers = {
            "Client-ID":     self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }
        body = f"""
            search "{game_name}";
            fields name, game_modes.name, genres.name,
                   platforms.name, involved_companies.company.name,
                   first_release_date;
            limit 1;
        """
        r = requests.post(
            "https://api.igdb.com/v4/games",
            headers=headers,
            data=body
        ).json()

        if not r:
            return {"name": game_name}

        g = r[0]
        modes = [m["name"] for m in g.get("game_modes", [])]
        genres = [genre["name"] for genre in g.get("genres", [])]
        platforms = [p["name"] for p in g.get("platforms", [])]

        return {
            "name":            game_name,
            "igdb_genres":     ", ".join(genres),
            "igdb_platforms":  ", ".join(platforms),
            "is_multiplayer":  "Multiplayer" in modes,
            "is_singleplayer": "Single player" in modes,
            "is_coop":         "Co-operative" in modes,
        }