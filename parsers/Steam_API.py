from base_parser import BaseParser
import requests
import time
import pandas as pd


class SteamAPIParser(BaseParser):
    BASE_URL = "https://store.steampowered.com/api/appdetails"

    def __init__(self, country_code: str = "us"): #здесь us тк много игр в России не доступно
       
        super().__init__("data/raw/steam_api", delay=1.5)
        self.country_code = country_code
        # Счётчики для статистики
        self.not_found = []
        self.wrong_type = []

    def parse_game(self, game_id: int) -> dict:
        try:
            # Добавляем параметр cc с кодом страны
            r = requests.get(
                self.BASE_URL,
                params={
                    "appids": game_id,
                    "l": "english",
                    "cc": self.country_code    
                },
                timeout=10
            ).json()
        except Exception as e:
            return {}

        data = r.get(str(game_id), {})
        if not data.get("success"):
            self.not_found.append(game_id)
            return {}

        d = data["data"]

        # Можно разрешить не только игры, но и демо/DLC
        if d.get("type") != "game":
            self.wrong_type.append(game_id)
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

    def parse_all(self, game_ids: list) -> pd.DataFrame:
        results = []
        total = len(game_ids)
        
        for i, game_id in enumerate(game_ids):
            print(f"{i+1}/{total}: Парсим {game_id}")
            
            data = self.parse_game(game_id)
            if data:
                results.append(data)
            
            time.sleep(self.delay)
        
        # Выводим статистику
        print(f"\n{'='*50}")
        print(f"Статистика парсинга (регион: {self.country_code})")
        print(f"{'='*50}")
        print(f"Всего игр в списке: {total}")
        print(f"Успешно спарсено: {len(results)}")
        print(f"Не найдено (удалены или скрыты): {len(self.not_found)}")
        print(f"Не игры (DLC, демо и т.д.): {len(self.wrong_type)}")
        
        if self.not_found:
            print(f"\nПримеры не найденных ID: {self.not_found[:10]}")
        
        return pd.DataFrame(results)


if __name__ == "__main__":
    import sys
    sys.path.append(".")

    game_ids = pd.read_csv("data/game_ids.csv")["steam_id"].tolist()
    print(f"Игр для парсинга: {len(game_ids)}")

    parser = SteamAPIParser(country_code="us")
    df = parser.parse_all(game_ids)
    
    print(f"\nГотово! Спарсено: {len(df)}")
    
    # Сохраняем результат
    df.to_csv("data/raw/steam_api/steam_games.csv", index=False)
    print("Результат сохранён в data/raw/steam_api/steam_games.csv")
