import requests
import pandas as pd
import time

def get_game_ids(limit: int = 1000) -> pd.DataFrame:
    print("Загружаем список всех игр Steam...")
    all_apps = requests.get(
        "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    ).json()["applist"]["apps"]

    print(f"Всего приложений в Steam: {len(all_apps)}")

    candidates = []
    checked = 0

    for app in all_apps:
        if len(candidates) >= limit:
            break

        app_id = app["appid"]
        name = app.get("name", "").strip()
        if not name:
            continue

        try:
            r = requests.get(
                "https://store.steampowered.com/api/appdetails",
                params={"appids": app_id, "l": "english"},
                timeout=10
            ).json()

            data = r.get(str(app_id), {})
            if not data.get("success"):
                continue

            d = data["data"]

            # фильтры
            if d.get("type") != "game":       # только игры, не DLC
                continue
            if d.get("release_date", {}).get("coming_soon"):
                continue

            candidates.append({
                "steam_id":     app_id,
                "name":         d.get("name"),
                "release_date": d.get("release_date", {}).get("date"),
            })
            print(f"[{len(candidates)}/{limit}] Добавлена: {name}")

        except Exception as e:
            print(f"Ошибка для {app_id}: {e}")

        checked += 1
        time.sleep(1.5)  # лимит Steam API

    df = pd.DataFrame(candidates)
    df.to_csv("data/game_ids.csv", index=False)
    print(f"\nГотово! Сохранено {len(df)} игр в data/game_ids.csv")
    return df


if name == "main":
    get_game_ids(limit=700)