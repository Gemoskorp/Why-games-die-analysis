import requests
import pandas as pd
import sys
import time
from base_parser import BaseParser


API_KEY = "39cd03824acf72e35afb49b131dc6d1902f9c6d8"


class IsTherAnyDealParser(BaseParser):
    def __init__(self):
        super().__init__("data/raw/isthereanydeal", delay=1.0)
        self.api_key = API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

    def _lookup_game_id(self, game_name: str) -> str | None:
        url = "https://api.isthereanydeal.com/games/lookup/v1"
        params = {"key": self.api_key, "title": game_name}

        for attempt in range(3):
            try:
                r = self.session.get(url, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
                if data.get("found"):
                    return data["game"]["id"]
                return None
            except requests.exceptions.Timeout:
                print(f"  Таймаут lookup попытка {attempt+1}/3")
                time.sleep(3)
            except Exception as e:
                print(f"  Ошибка lookup: {e}")
                return None

        return None

    def _get_prices(self, game_id: str) -> dict:
        url = "https://api.isthereanydeal.com/games/prices/v3"
        params = {"key": self.api_key, "country": "US"}

        try:
            r = self.session.post(url, params=params, json=[game_id], timeout=15)
            r.raise_for_status()
            data = r.json()

            if not data:
                return {}

            entry = data[0]
            deals = entry.get("deals", [])

            # исторические минимумы
            history_low = entry.get("historyLow", {}) or {}
            history_low_all = history_low.get("all", {})
            history_low_y1  = history_low.get("y1", {})
            history_low_m3  = history_low.get("m3", {})

            history = {
                "history_low_all": history_low_all.get("amount") if history_low_all else None,
                "history_low_y1":  history_low_y1.get("amount")  if history_low_y1  else None,
                "history_low_m3":  history_low_m3.get("amount")  if history_low_m3  else None,
            }

            if not deals:
                return {"has_discount": None, **history}

            # free-to-play — все deals с ценой 0
            if all(d["price"]["amount"] == 0 for d in deals):
                return {
                    "has_discount":  None,
                    "discount_pct":  None,
                    "current_price": 0,
                    "regular_price": 0,
                    "best_shop":     deals[0]["shop"]["name"],
                    "is_free":       True,
                    **history,
                }

            # берём deal с максимальной скидкой
            best = max(deals, key=lambda d: d.get("cut", 0))
            cut           = best.get("cut", 0)
            current_price = best["price"]["amount"]
            regular_price = best.get("regular", {}).get("amount")

            return {
                "has_discount":  cut > 0,
                "discount_pct":  cut if cut > 0 else 0,
                "current_price": current_price,
                "regular_price": regular_price,
                "best_shop":     best["shop"]["name"],
                "is_free":       False,
                **history,
            }

        except Exception as e:
            print(f"  Ошибка prices: {e}")
            return {}

    def parse_game(self, game_name: str) -> dict | None:
        game_id = self._lookup_game_id(game_name)
        if not game_id:
            print(f"  Не найдено: {game_name}")
            return None

        prices = self._get_prices(game_id)

        print(
            f"  discount={prices.get('discount_pct')}% | "
            f"price={prices.get('current_price')} | "
            f"free={prices.get('is_free')} | "
            f"low_all={prices.get('history_low_all')}"
        )

        return {
            "name":            game_name,
            "itad_id":         game_id,
            "is_free":         prices.get("is_free"),
            "has_discount":    prices.get("has_discount"),
            "discount_pct":    prices.get("discount_pct"),
            "current_price":   prices.get("current_price"),
            "regular_price":   prices.get("regular_price"),
            "best_shop":       prices.get("best_shop"),
            "history_low_all": prices.get("history_low_all"),
            "history_low_y1":  prices.get("history_low_y1"),
            "history_low_m3":  prices.get("history_low_m3"),
        }

if __name__ == "__main__":
    sys.path.append(".")

    game_names = pd.read_csv("data/game_ids.csv")["name"].tolist()
    print(f"Игр для парсинга: {len(game_names)}")

    parser = IsTherAnyDealParser()
    df = parser.parse_all(game_names)

    # насколько упала цена от обычной до исторического минимума
    # например: regular=20$, history_low=5$ → drop=75%
    mask = (
        df["regular_price"].notna() &
        df["history_low_all"].notna() &
        (df["regular_price"] > 0) &
        (df["is_free"] != True)
    )
    df.loc[mask, "history_low_drop_all_pct"] = (
        (df["regular_price"] - df["history_low_all"]) / df["regular_price"] * 100
    ).round(1)

    df.loc[mask, "history_low_drop_y1_pct"] = (
        (df["regular_price"] - df["history_low_y1"]) / df["regular_price"] * 100
    ).round(1)

    df.loc[mask, "history_low_drop_m3_pct"] = (
        (df["regular_price"] - df["history_low_m3"]) / df["regular_price"] * 100
    ).round(1)

    print(f"\nГотово! Всего: {len(df)}")
    print(f"Со скидкой:    {len(df[df['has_discount'] == True])}")
    print(f"Без скидки:    {len(df[df['has_discount'] == False])}")
    print(f"Бесплатных:    {len(df[df['is_free'] == True])}")
    print(df[df["has_discount"] == True][
        ["name", "discount_pct", "history_low_drop_all_pct", "history_low_drop_m3_pct"]
    ].head(20))