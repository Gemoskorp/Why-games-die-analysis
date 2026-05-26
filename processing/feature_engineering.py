import json
import math
from pathlib import Path
import pandas as pd


PROCESSED_DIR = Path("data/processed")


def to_number(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)
    text = str(value).replace("%", "").replace(",", "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


class FeatureEngineer:
    """
    Берёт games_dataset.csv после merger.py и делает таблицу features.csv для модели.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def _parse_history(self, history_json):
        if pd.isna(history_json):
            return []
        try:
            history = json.loads(history_json)
        except Exception:
            return []

        if not isinstance(history, list):
            return []

        cleaned = []
        for item in history:
            if not isinstance(item, dict):
                continue

            avg = item.get("avg_players", item.get("avg_online"))
            peak = item.get("peak")
            cleaned.append({
                "month": item.get("month"),
                "avg_online": to_number(avg) or 0.0,
                "peak": to_number(peak) or 0.0,
            })

        # SteamCharts обычно идёт от нового месяца к старому.
        # Для анализа удобнее от старого к новому.
        return list(reversed(cleaned))

    def add_online_features(self):
        if "history" not in self.df.columns:
            self.df["history"] = None

        parsed = self.df["history"].apply(self._parse_history)

        self.df["months_observed"] = parsed.apply(len)
        self.df["current_avg_online"] = parsed.apply(lambda h: h[-1]["avg_online"] if h else 0)
        self.df["max_avg_online"] = parsed.apply(lambda h: max([x["avg_online"] for x in h], default=0))
        self.df["avg_online_3m"] = parsed.apply(lambda h: sum(x["avg_online"] for x in h[-3:]) / min(len(h), 3) if h else 0)
        self.df["avg_online_12m"] = parsed.apply(lambda h: sum(x["avg_online"] for x in h[-12:]) / min(len(h), 12) if h else 0)
        self.df["peak_from_history"] = parsed.apply(lambda h: max([x["peak"] for x in h], default=0))

        def decline_from_peak(h):
            if not h:
                return 0
            peak = max(x["avg_online"] for x in h)
            current = h[-1]["avg_online"]
            if peak <= 0:
                return 0
            return 1 - current / peak

        def months_since_peak(h):
            if not h:
                return None
            values = [x["avg_online"] for x in h]
            peak_i = values.index(max(values))
            return len(values) - 1 - peak_i

        def trend_3m(h):
            if len(h) < 4:
                return 0
            return h[-1]["avg_online"] - h[-4]["avg_online"]

        self.df["decline_from_peak"] = parsed.apply(decline_from_peak)
        self.df["months_since_peak"] = parsed.apply(months_since_peak)
        self.df["trend_3m"] = parsed.apply(trend_3m)
        return self

    def add_death_label(self):
        """
        is_dead:
        1 — игра условно умерла,
        0 — нет.

        Если SteamCharts уже дал is_dead — используем его.
        Если нет — считаем сами: текущий средний онлайн меньше 1/3 от максимального среднего онлайна.
        """
        if "is_dead" in self.df.columns:
            existing = pd.to_numeric(self.df["is_dead"], errors="coerce")
        else:
            existing = pd.Series([None] * len(self.df), index=self.df.index)

        computed = (
            (self.df.get("max_avg_online", 0) > 0) &
            (self.df.get("current_avg_online", 0) < self.df.get("max_avg_online", 0) / 3)
        ).astype(int)

        self.df["is_dead"] = existing.fillna(computed).astype(int)
        return self

    def add_other_features(self):
        numeric_cols = [
            "peak_all_time", "peak_24h", "price_usd", "achievements",
            "languages_count", "total_reviews", "total_positive", "total_negative",
            "positive_ratio", "hltb_main", "hltb_extra", "hltb_complete",
            "current_price", "regular_price", "discount_pct",
            "history_low_all", "history_low_y1", "history_low_m3",
        ]
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        if "genres" in self.df.columns:
            genres = self.df["genres"].fillna("").str.lower()
            self.df["is_multiplayer"] = genres.str.contains("massively multiplayer|mmo|multiplayer").astype(int)
            self.df["is_singleplayer"] = (~genres.str.contains("massively multiplayer|mmo")).astype(int)
        else:
            self.df["is_multiplayer"] = 0
            self.df["is_singleplayer"] = 1

        # Метаскора у вас сейчас нет, поэтому score_gap делаем только если колонки реально есть.
        if "metascore" in self.df.columns and "user_score" in self.df.columns:
            self.df["metascore"] = pd.to_numeric(self.df["metascore"], errors="coerce")
            self.df["user_score"] = pd.to_numeric(self.df["user_score"], errors="coerce")
            self.df["score_gap"] = (self.df["metascore"] - self.df["user_score"] * 10).abs()

        return self

    def run(self):
        self.add_online_features()
        self.add_death_label()
        self.add_other_features()
        return self.df


if __name__ == "__main__":
    input_path = PROCESSED_DIR / "games_dataset.csv"
    output_path = PROCESSED_DIR / "features.csv"

    df = pd.read_csv(input_path)
    features = FeatureEngineer(df).run()
    features.to_csv(output_path, index=False)

    print(f"Готово: {output_path}")
    print(f"Размер: {features.shape[0]} строк × {features.shape[1]} колонок")
