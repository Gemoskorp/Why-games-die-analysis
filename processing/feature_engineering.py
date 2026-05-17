import pandas as pd
import json

class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def compute_death_label(self) -> pd.DataFrame:
        self.df["is_dead"] = self.df["online_history"].apply(self._check_death)
        return self.df

    def _check_death(self, history_json: str) -> bool:
        try:
            history = json.loads(history_json)
        except:
            return False
        if len(history) < 4:
            return False

        baseline = history[3]["avg_online"]  # онлайн через 3 месяца после релиза
        if baseline == 0:
            return True

        dead_streak = 0
        for entry in history[4:]:
            ratio = entry["avg_online"] / baseline
            if ratio < (1 / 3):  # упал в 3+ раза от базовой точки
                dead_streak += 1
            else:
                dead_streak = 0
            if dead_streak >= 36:  # 3 года подряд
                return True
        return False

    def compute_death_speed(self) -> pd.DataFrame:
        self.df["months_to_death"] = self.df["online_history"].apply(
            self._months_until_death
        )
        return self.df

    def _months_until_death(self, history_json: str):
        try:
            history = json.loads(history_json)
        except:
            return None
        if not history:
            return None
        peak = max(e["avg_online"] for e in history)
        for i, entry in enumerate(history):
            if peak > 0 and peak / max(entry["avg_online"], 1) >= 3:
                return i
        return None

    def compute_score_gap(self) -> pd.DataFrame:
        self.df["score_gap"] = abs(
            self.df["metascore"].astype(float) -
            self.df["user_score"].astype(float) * 10
        )
        return self.df