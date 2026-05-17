import requests
import pandas as pd
import time


def get_game_ids(limit_per_group: int = 250):
    print("Загружаем игры через SteamSpy...")

    all_games = {}
    for page in range(10):  # берём 10 страниц = ~10000 игр
        r = requests.get(
            "https://steamspy.com/api.php",
            params={"request": "all", "page": page},
            timeout=30
        )
        if r.status_code != 200:
            print(f"Страница {page}: ошибка {r.status_code}, останавливаемся")
            break
        all_games.update(r.json())
        print(f"Страница {page}: всего {len(all_games)} игр собрано")
        time.sleep(2)  # SteamSpy просит не спамить

    print(f"\nВсего игр получено: {len(all_games)}")

    # превращаем в датафрейм
    candidates = []
    for app_id, info in all_games.items():
        name = info.get("name", "").strip()
        if not name:
            continue
        candidates.append({
            "steam_id": int(app_id),
            "name":     name,
            "owners":   info.get("owners", ""),
            "positive": info.get("positive", 0),
            "negative": info.get("negative", 0),
        })

    df = pd.DataFrame(candidates)

    # --- группа 1: маленькие игры (скорее всего мёртвые) ---
    small_mask = (
        df["owners"].str.startswith("0 ..") |
        df["owners"].str.startswith("20,000 ..") |
        df["owners"].str.startswith("50,000 ..")
    )
    small = df[small_mask].sample(
        min(limit_per_group, small_mask.sum()), random_state=42
    )

    # --- группа 2: средние игры ---
    medium_mask = (
        df["owners"].str.startswith("200,000 ..") |
        df["owners"].str.startswith("500,000 ..")
    )
    medium = df[medium_mask].sample(
        min(limit_per_group, medium_mask.sum()), random_state=42
    )

    # --- группа 3: крупные игры (скорее всего живые) ---
    large_mask = (
        df["owners"].str.startswith("2,000,000 ..") |
        df["owners"].str.startswith("5,000,000 ..")
    )
    large = df[large_mask].sample(
        min(limit_per_group, large_mask.sum()), random_state=42
    )

    # объединяем все три группы
    result = pd.concat([small, medium, large]).drop_duplicates("steam_id")
    result = result.reset_index(drop=True)

    # сохраняем
    result.to_csv("data/game_ids.csv", index=False)

    print(f"\nГотово! Итого {len(result)} игр:")
    print(f"  Маленькие (вероятно мёртвые): {len(small)}")
    print(f"  Средние:                      {len(medium)}")
    print(f"  Крупные (вероятно живые):     {len(large)}")
    print(result.head())
    return result


if __name__ == "__main__":
    get_game_ids(limit_per_group=250)









import pandas as pd

df = pd.read_csv("data/game_ids.csv")

# добавляем метку группы для наглядности
def get_group(owners):
    if any(owners.startswith(x) for x in ["0 ..", "20,000 ..", "50,000 .."]):
        return "маленькая"
    elif any(owners.startswith(x) for x in ["200,000 ..", "500,000 .."]):
        return "средняя"
    else:
        return "крупная"

df["group"] = df["owners"].apply(get_group)

print("Маленькие игры (первые 5):")
print(df[df["group"] == "маленькая"][["name", "owners"]].head())

print("\nСредние игры (первые 5):")
print(df[df["group"] == "средняя"][["name", "owners"]].head())

print("\nКрупные игры (первые 5):")
print(df[df["group"] == "крупная"][["name", "owners"]].head())






# import requests
# import pandas as pd
# import time
# def get_game_ids(limit: int = 700):
#     print("Загружаем список игр через SteamSpy...")
    
#     all_games = {}
    
#     # SteamSpy отдаёт по 1000 игр на страницу
#     for page in range(3):  # 3 страницы = ~3000 игр, выберем лучшие
#         response = requests.get(
#             "https://steamspy.com/api.php",
#             params={"request": "all", "page": page},
#             timeout=30
#         )
#         print(f"Страница {page}: статус {response.status_code}")
        
#         if response.status_code != 200:
#             break
            
#         data = response.json()
#         all_games.update(data)
#         print(f"Всего игр собрано: {len(all_games)}")
#         time.sleep(2)  # SteamSpy просит не спамить
    
#     # превращаем в список
#     candidates = []
#     for app_id, info in all_games.items():
#         name = info.get("name", "").strip()
#         if not name:
#             continue
            
#         # фильтр — берём игры у которых был хоть какой-то онлайн
#         owners = info.get("owners", "0 .. 0")
        
#         candidates.append({
#             "steam_id": int(app_id),
#             "name":     name,
#             "owners":   owners,
#             "peak_ccu": info.get("peak_ccu", 0),
#         })
    
#     # сортируем по пиковому онлайну — берём самые популярные
#     candidates.sort(key=lambda x: x["peak_ccu"], reverse=True)
#     candidates = candidates[:limit]
    
#     df = pd.DataFrame(candidates)
#     df.to_csv("data/game_ids.csv", index=False)
#     print(f"\nГотово! Сохранено {len(df)} игр в data/game_ids.csv")
#     print(df.head())
#     return df

# if __name__ == "__main__":
#     get_game_ids(limit=700)