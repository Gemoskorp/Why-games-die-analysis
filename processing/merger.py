import pandas as pd
from pathlib import Path

class Merger:
    def init(self):
        self.raw_dir = Path("data/raw")

    def load_all(self) -> pd.DataFrame:
        print("Загружаем все датасеты...")

        steam     = self._load("steam_api")
        steamdb   = self._load("steamdb")
        reviews   = self._load("steam_reviews")
        metacritic = self._load("metacritic")
        hltb      = self._load("hltb")
        igdb      = self._load("igdb")

        print("Объединяем...")

        # основа — steam_api, у него есть steam_id у всех игр
        df = steam

        # джойним по steam_id
        df = df.merge(steamdb,   on="steam_id", how="left", suffixes=("", "_steamdb"))
        df = df.merge(reviews,   on="steam_id", how="left", suffixes=("", "_reviews"))

        # metacritic джойним по name (у него нет steam_id)
        if metacritic is not None:
            metacritic["name_lower"] = metacritic["slug"].str.replace("-", " ").str.lower()
            df["name_lower"] = df["name"].str.lower()
            df = df.merge(
                metacritic, on="name_lower", how="left", suffixes=("", "_meta")
            )
            df.drop(columns=["name_lower"], inplace=True)

        # hltb и igdb джойним по name
        if hltb is not None:
            hltb["name_lower"] = hltb["name"].str.lower()
            df["name_lower"] = df["name"].str.lower()
            df = df.merge(hltb, on="name_lower", how="left", suffixes=("", "_hltb"))
            df.drop(columns=["name_lower"], inplace=True)

        if igdb is not None:
            igdb["name_lower"] = igdb["name"].str.lower()
            df["name_lower"] = df["name"].str.lower()
            df = df.merge(igdb, on="name_lower", how="left", suffixes=("", "_igdb"))
            df.drop(columns=["name_lower"], inplace=True)

        # убираем дубли колонок
        df = df.loc[:, ~df.columns.duplicated()]

        output = Path("data/processed")
        output.mkdir(parents=True, exist_ok=True)
        df.to_csv(output / "games_data
