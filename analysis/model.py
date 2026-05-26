import pandas as pd
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import json

class MortalityModel:
    FEATURES = [
        "metascore",
        "user_score",
        "peak_all_time",
        "price_usd",
        "achievements",
        "languages_count",
        "is_multiplayer",
        "is_singleplayer",
        "positive_ratio",
        "hltb_main",
        "score_gap",
    ]

    def init(self, df: pd.DataFrame):
        self.df = self._prepare(df)
        self.model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced"  # важно если мёртвых игр меньше чем живых
        )

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()

        # приводим типы
        for col in ["metascore", "user_score", "peak_all_time",
                    "price_usd", "achievements", "hltb_main",
                    "languages_count", "positive_ratio", "score_gap"]:
            if col in d.columns:
                d[col] = pd.to_numeric(d[col], errors="coerce")

        # булевые → числа
        for col in ["is_multiplayer", "is_singleplayer"]:
            if col in d.columns:
                d[col] = d[col].astype(float)

        # убираем строки без целевой переменной
        d = d.dropna(subset=["is_dead"])

        # заполняем пропуски медианой
        for col in self.FEATURES:
            if col in d.columns:
                d[col] = d[col].fillna(d[col].median())

        return d

    def train(self):
        available = [f for f in self.FEATURES if f in self.df.columns]

        X = self.df[available]
        y = self.df["is_dead"]

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        self.model.fit(self.X_train, self.y_train)
        self.used_features = available

        preds = self.model.predict(self.X_test)
        print(f"Accuracy: {accuracy_score(self.y_test, preds):.2%}")
        print(classification_report(self.y_test, preds,
                                     target_names=["Живая", "Мёртвая"]))

    def feature_importance_chart(self) -> go.Figure:
        importances = pd.Series(
            self.model.feature_importances_,
            index=self.used_features
        ).sort_values(ascending=True)

        # человекочитаемые названия
        labels = {
            "metascore":       "Metascore",
            "user_score":      "User Score",
            "peak_all_time":   "Пиковый онлайн",
            "price_usd":       "Цена ($)",
            "achievements":    "Кол-во достижений",
            "languages_count": "Кол-во языков",
            "is_multiplayer":  "Мультиплеер",
            "is_singleplayer": "Одиночная",
            "positive_ratio":  "Доля позит. отзывов",
            "hltb_main":       "Время прохождения (ч)",
            "score_gap":       "Разрыв оценок",
        }

        fig = go.Figure(go.Bar(
            x=importances.values,
            y=[labels.get(f, f) for f in importances.index],
            orientation="h",
            marker_color="steelblue",
        ))
        fig.update_layout(
            title="Топ факторов влияющих на выживаемость игры",
            xaxis_title="Важность признака",
            height=400,
        )
        return fig

    def predict_game(self, game_data: dict) -> dict:
        """Предсказание для одной игры"""
        X = pd.DataFrame([game_data])[self.used_features]
        proba = self.model.predict_proba(X)[0][1]
        return {
            "death_probability": round(proba, 3),
            "verdict": "Мёртвая" if proba > 0.5 else "Живая",
            "confidence": f"{max(proba, 1-proba):.0%}",
        }
if name == "main":
    df = pd.read_csv("data/processed/features.csv")
    model = MortalityModel(df)
    model.train()
    fig = model.feature_importance_chart()
    fig.show()
