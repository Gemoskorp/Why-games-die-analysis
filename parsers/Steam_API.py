# scripts/get_game_ids.py
import requests
import json
import pandas as pd

def get_game_ids():
    # Шаг 1 — берём все игры из Steam (их ~100k+)
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    all_apps = requests.get(url).json()["applist"]["apps"]
    
    # Шаг 2 — для каждой игры запрашиваем детали
    # (делаем только для кандидатов чтобы не парсить 100k игр)
    candidates = []
    
    for app in all_apps[:5000]:  # берём первые 5000 для теста
        app_id = app["appid"]
        
        detail_url = "https://store.steampowered.com/api/appdetails"
        r = requests.get(detail_url, params={"appids": app_id}).json()
        data = r.get(str(app_id), {})
        
        if not data.get("success"):
            continue
        
        d = data["data"]
        
        # фильтры — берём только нормальные игры
        if d.get("type") != "game":          # убираем DLC, саундтреки
            continue
        if d.get("is_free") == False:
            price = d.get("price_overview", {}).get("final", 0)
            if price == 0:                   # убираем игры без цены
                continue
        
        release = d.get("release_date", {})
        if release.get("coming_soon"):        # убираем неvышедшие
            continue
            
        candidates.append({
            "steam_id": app_id,
            "name": d.get("name"),
            "release_date": release.get("date"),
        })
    
    # Шаг 3 — сохраняем
    df = pd.DataFrame(candidates)
    df.to_csv("data/game_ids.csv", index=False)
    print(f"Найдено игр: {len(df)}")
    return df

if __name__ == "__main__":
    get_game_ids()