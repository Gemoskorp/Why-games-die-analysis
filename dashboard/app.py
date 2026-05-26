from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import joblib
from dash import Dash, dcc, html, Input, Output


DATA_PATH = Path("data/processed/features.csv")
IMPORTANCE_PATH = Path("data/processed/feature_importance.csv")
MODEL_PATH = Path("models/mortality_model.joblib")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        "Нет data/processed/features.csv. Сначала запусти merger.py, потом feature_engineering.py"
    )

df = pd.read_csv(DATA_PATH)

model_bundle = None
if MODEL_PATH.exists():
    try:
        model_bundle = joblib.load(MODEL_PATH)
    except Exception:
        model_bundle = None

app = Dash(__name__)

BLUE_BG = "#eef5ff"
CARD_BG = "#ffffff"
DARK_BLUE = "#173b63"
MID_BLUE = "#5b8fc9"
SOFT_BLUE = "#78a6d8"
DEAD_BLUE = "#3d6f9f"
ALIVE_BLUE = "#8bbce8"
GRID = "#d8e6f5"
TEXT = "#203040"

FEATURE_LABELS = {
    "peak_all_time": "Максимальный разовый онлайн",
    "peak_24h": "Пик онлайна за последние 24 часа",
    "price_usd": "Цена в Steam",
    "achievements": "Количество достижений",
    "languages_count": "Количество поддерживаемых языков",
    "total_reviews": "Количество отзывов",
    "positive_ratio": "Доля положительных отзывов",
    "hltb_main": "Длина основного прохождения",
    "hltb_complete": "Длина полного прохождения",
    "current_price": "Текущая цена",
    "regular_price": "Обычная цена без скидки",
    "discount_pct": "Размер скидки",
    "history_low_all": "Исторический минимум цены",
    "history_low_y1": "Минимальная цена за год",
    "history_low_m3": "Минимальная цена за 3 месяца",
    "is_multiplayer": "Есть мультиплеер",
    "is_singleplayer": "Одиночная игра",
    "metascore": "Оценка критиков",
    "user_score": "Оценка игроков",
    "score_gap": "Разрыв оценок критиков и игроков",
}


def split_genres(value):
    if pd.isna(value):
        return []
    return [g.strip() for g in str(value).split(",") if g.strip()]


def status_text(value):
    try:
        return "Мёртвая" if int(value) == 1 else "Живая"
    except Exception:
        return "Неизвестно"


def status_color(value):
    try:
        return DEAD_BLUE if int(value) == 1 else ALIVE_BLUE
    except Exception:
        return MID_BLUE


def apply_figure_style(fig):
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor="#f8fbff",
        font={"family": "Arial", "color": TEXT},
        title={"font": {"color": DARK_BLUE, "size": 20}},
        margin={"l": 70, "r": 30, "t": 70, "b": 70},
        legend={
            "bgcolor": "rgba(255,255,255,0.75)",
            "bordercolor": GRID,
            "borderwidth": 1,
        },
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


all_genres = sorted({g for value in df.get("genres", pd.Series(dtype=str)) for g in split_genres(value)})

# Для окна предсказания показываем только живые игры.
if "is_dead" in df.columns:
    alive_df = df[pd.to_numeric(df["is_dead"], errors="coerce").fillna(0).astype(int) == 0].copy()
else:
    alive_df = df.copy()

# Фиксируем масштаб первого графика один раз по всей таблице.
# Теперь при выборе "живые" или "мёртвые" шкала не будет прыгать.
SCATTER_X_COL = "positive_ratio" if "positive_ratio" in df.columns else "total_reviews"
SCATTER_Y_COL = "peak_all_time" if "peak_all_time" in df.columns else "max_avg_online"
SCATTER_X_RANGE = [0, 1] if SCATTER_X_COL == "positive_ratio" else None
_y_values = pd.to_numeric(df.get(SCATTER_Y_COL, pd.Series(dtype=float)), errors="coerce").dropna()
_y_values = _y_values[_y_values > 0]
if len(_y_values):
    import math
    SCATTER_Y_RANGE = [
        math.log10(max(_y_values.min() * 0.9, 0.1)),
        math.log10(_y_values.max() * 1.08),
    ]
else:
    SCATTER_Y_RANGE = [0, 1]

app.layout = html.Div(
    style={
        "background": BLUE_BG,
        "minHeight": "100vh",
        "padding": "28px",
        "fontFamily": "Arial, sans-serif",
        "color": TEXT,
    },
    children=[
        html.Div(
            style={"maxWidth": "1180px", "margin": "0 auto"},
            children=[
                html.Div(
                    style={
                        "background": f"linear-gradient(135deg, {DARK_BLUE}, {MID_BLUE})",
                        "borderRadius": "22px",
                        "padding": "28px 34px",
                        "boxShadow": "0 12px 35px rgba(23, 59, 99, 0.18)",
                        "color": "white",
                        "marginBottom": "22px",
                    },
                    children=[
                        html.H1("Why Games Die: An Analysis", style={"margin": "0", "fontSize": "34px"}),
                        html.P(
                            "Дашборд про признаки, которые связаны с падением активности игр.",
                            style={"margin": "8px 0 0", "opacity": "0.88", "fontSize": "16px"},
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "background": CARD_BG,
                        "borderRadius": "18px",
                        "padding": "20px",
                        "boxShadow": "0 8px 24px rgba(23, 59, 99, 0.10)",
                        "marginBottom": "22px",
                    },
                    children=[
                        html.Div(
                            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "20px"},
                            children=[
                                html.Div([
                                    html.Label("Жанр", style={"fontWeight": "bold", "color": DARK_BLUE}),
                                    dcc.Dropdown(
                                        id="genre-filter",
                                        options=[{"label": g, "value": g} for g in all_genres],
                                        multi=True,
                                        placeholder="Все жанры",
                                    ),
                                ]),
                                html.Div([
                                    html.Label("Статус", style={"fontWeight": "bold", "color": DARK_BLUE}),
                                    dcc.RadioItems(
                                        id="status-filter",
                                        options=[
                                            {"label": "Все", "value": "all"},
                                            {"label": "Живые", "value": "alive"},
                                            {"label": "Мёртвые", "value": "dead"},
                                        ],
                                        value="all",
                                        inline=True,
                                        style={"marginTop": "10px"},
                                        inputStyle={"marginRight": "6px", "marginLeft": "12px"},
                                    ),
                                ]),
                            ],
                        ),
                        html.Div(
                            id="filter-summary",
                            style={
                                "marginTop": "14px",
                                "padding": "10px 14px",
                                "borderRadius": "12px",
                                "background": "#f1f7ff",
                                "color": DARK_BLUE,
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "background": CARD_BG,
                        "borderRadius": "18px",
                        "padding": "14px",
                        "boxShadow": "0 8px 24px rgba(23, 59, 99, 0.10)",
                        "marginBottom": "22px",
                    },
                    children=[dcc.Graph(id="feature-importance-plot")],
                ),
                html.Div(
                    style={
                        "background": CARD_BG,
                        "borderRadius": "18px",
                        "padding": "20px",
                        "boxShadow": "0 8px 24px rgba(23, 59, 99, 0.10)",
                        "marginBottom": "22px",
                    },
                    children=[
                        html.H3("Предсказание для игры", style={"marginTop": "0", "color": DARK_BLUE}),
                        html.P(
                            "Выбери живую игру — модель оценит риск ухода в низкий онлайн.",
                            style={"marginTop": "0", "color": TEXT},
                        ),
                        dcc.Dropdown(
                            id="predict-game-search",
                            options=[
                                {"label": row.get("name", str(row.get("steam_id"))), "value": row.get("steam_id")}
                                for _, row in alive_df.dropna(subset=["steam_id"]).iterrows()
                            ],
                            placeholder="Например: Dawn of Defiance",
                            searchable=True,
                        ),
                        html.Div(id="prediction-result", style={"marginTop": "14px"}),
                    ],
                ),
                html.Div(
                    style={
                        "background": CARD_BG,
                        "borderRadius": "18px",
                        "padding": "20px",
                        "boxShadow": "0 8px 24px rgba(23, 59, 99, 0.10)",
                        "marginBottom": "22px",
                    },
                    children=[
                        html.Label("Найти игру", style={"fontWeight": "bold", "color": DARK_BLUE}),
                        dcc.Dropdown(
                            id="game-search",
                            options=[
                                {"label": row.get("name", str(row.get("steam_id"))), "value": row.get("steam_id")}
                                for _, row in df.dropna(subset=["steam_id"]).iterrows()
                            ],
                            placeholder="Введи название игры...",
                            searchable=True,
                        ),
                        html.Div(id="selected-game-status", style={"marginTop": "12px"}),
                        dcc.Graph(id="online-history-plot"),
                    ],
                ),
                html.Div(
                    style={
                        "background": CARD_BG,
                        "borderRadius": "18px",
                        "padding": "14px",
                        "boxShadow": "0 8px 24px rgba(23, 59, 99, 0.10)",
                    },
                    children=[dcc.Graph(id="scatter-plot")],
                ),
            ],
        )
    ],
)


@app.callback(
    Output("scatter-plot", "figure"),
    Output("filter-summary", "children"),
    Input("genre-filter", "value"),
    Input("status-filter", "value"),
)
def update_scatter(genres, status):
    filtered = df.copy()

    if genres and "genres" in filtered.columns:
        filtered = filtered[filtered["genres"].fillna("").apply(lambda s: any(g in split_genres(s) for g in genres))]

    if status == "alive":
        filtered = filtered[filtered["is_dead"] == 0]
    elif status == "dead":
        filtered = filtered[filtered["is_dead"] == 1]

    alive_count = int((filtered.get("is_dead", pd.Series(dtype=int)) == 0).sum()) if "is_dead" in filtered.columns else 0
    dead_count = int((filtered.get("is_dead", pd.Series(dtype=int)) == 1).sum()) if "is_dead" in filtered.columns else 0
    summary = f"Показано игр: {len(filtered)} | Живые: {alive_count} | Мёртвые: {dead_count}"

    if filtered.empty:
        fig = go.Figure()
        fig.update_layout(title="Нет игр под выбранные фильтры")
        return apply_figure_style(fig), summary

    filtered = filtered.copy()
    filtered["Статус игры"] = filtered["is_dead"].map({0: "Живая", 1: "Мёртвая"})

    fig = px.scatter(
        filtered,
        x=SCATTER_X_COL,
        y=SCATTER_Y_COL,
        color="Статус игры",
        hover_name="name" if "name" in filtered.columns else None,
        hover_data={
            "steam_id": True if "steam_id" in filtered.columns else False,
            "positive_ratio": ":.2f" if "positive_ratio" in filtered.columns else False,
            "peak_all_time": True if "peak_all_time" in filtered.columns else False,
            "Статус игры": True,
        },
        title="Связь отзывов и пикового онлайна",
        color_discrete_map={"Живая": ALIVE_BLUE, "Мёртвая": DEAD_BLUE},
    )

    fig.update_traces(marker={"size": 9, "opacity": 0.78, "line": {"width": 0.8, "color": "white"}})
    fig.update_layout(
        xaxis_title="Доля положительных отзывов",
        yaxis_title="Пик по онлайн игрокам",
        yaxis_type="log",
    )

    if SCATTER_X_RANGE:
        fig.update_xaxes(range=SCATTER_X_RANGE, tickformat=".0%")
    fig.update_yaxes(
        range=SCATTER_Y_RANGE,
        showgrid=True,
        showticklabels=True,
        ticks="outside",
        dtick=1,  # для логарифмической шкалы: линия на 1, 10, 100, 1000 и т.д.
    )

    return apply_figure_style(fig), summary


@app.callback(
    Output("selected-game-status", "children"),
    Output("online-history-plot", "figure"),
    Input("game-search", "value"),
)
def update_online_history(steam_id):
    if steam_id is None:
        fig = go.Figure().update_layout(title="Выбери игру, чтобы увидеть историю онлайна")
        return "", apply_figure_style(fig)

    row = df[df["steam_id"] == steam_id]
    if row.empty:
        fig = go.Figure().update_layout(title="Игра не найдена")
        return "Игра не найдена", apply_figure_style(fig)

    row = row.iloc[0]
    game_status = status_text(row.get("is_dead"))
    color = status_color(row.get("is_dead"))

    badge = html.Div(
        style={
            "display": "inline-block",
            "padding": "9px 14px",
            "borderRadius": "999px",
            "background": color,
            "color": "white",
            "fontWeight": "bold",
        },
        children=f"Статус выбранной игры: {game_status}",
    )

    try:
        history = json.loads(row.get("history", "[]"))
    except Exception:
        history = []

    if not history:
        fig = go.Figure().update_layout(title=f"Нет истории онлайна: {row.get('name', steam_id)}")
        return badge, apply_figure_style(fig)

    history = list(reversed(history))
    months = [h.get("month") for h in history]

    def safe_float(v):
        try:
            return float(str(v).replace(",", ""))
        except Exception:
            return 0.0

    avg_online = [safe_float(h.get("avg_players", h.get("avg_online", 0))) for h in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=avg_online,
        mode="lines+markers",
        name="Средний онлайн",
        line={"color": MID_BLUE, "width": 3},
        marker={"size": 7, "color": SOFT_BLUE, "line": {"color": "white", "width": 1}},
    ))

    # Показываем подписи снизу не каждый месяц, а примерно раз в год.
    # Если данных мало — показываем чаще, но всё равно не вертикально.
    tick_step = 12 if len(months) > 24 else 6 if len(months) > 12 else 1
    tick_vals = months[::tick_step]

    fig.update_layout(
        title=f"История онлайна: {row.get('name', steam_id)} — {game_status}",
        xaxis_title="Год / месяц",
        yaxis_title="Средний онлайн игроков",
    )
    fig.update_xaxes(tickmode="array", tickvals=tick_vals, tickangle=-35)

    return badge, apply_figure_style(fig)


@app.callback(
    Output("feature-importance-plot", "figure"),
    Input("scatter-plot", "figure"),
)
def update_feature_importance(_):
    if not IMPORTANCE_PATH.exists():
        fig = go.Figure().update_layout(title="Сначала запусти model.py, чтобы получить feature_importance.csv")
        return apply_figure_style(fig)

    imp = pd.read_csv(IMPORTANCE_PATH)
    imp = imp[imp["feature"] != "is_singleplayer"]
    imp = imp.sort_values("importance", ascending=True)
    imp = imp.copy()
    imp["label"] = imp["feature"].map(FEATURE_LABELS).fillna(imp["feature"])

    fig = go.Figure(go.Bar(
        x=imp["importance"],
        y=imp["label"],
        orientation="h",
        marker={
            "color": imp["importance"],
            "colorscale": [[0, "#b7d6f2"], [1, DARK_BLUE]],
            "line": {"color": "white", "width": 0.7},
        },
        text=imp["importance"].round(3),
        textposition="outside",
    ))
    fig.update_layout(
        title="Важность факторов для модели",
        xaxis_title="Чем больше число, тем сильнее фактор использовался моделью",
        yaxis_title="",
        height=max(520, 28 * len(imp) + 170),
        margin={"l": 260, "r": 60, "t": 70, "b": 70},
        showlegend=False,
    )
    return apply_figure_style(fig)


def estimate_death_horizon(probability):
    """Очень грубая оценка срока. Это не отдельная модель времени, а интерпретация риска."""
    if probability >= 0.80:
        return "высокий риск в ближайшие 6–12 месяцев"
    if probability >= 0.60:
        return "заметный риск в течение 1–2 лет"
    if probability >= 0.40:
        return "средний риск, срок неочевиден"
    if probability >= 0.25:
        return "низкий риск в ближайшее время"
    return "очень низкий риск по текущим данным"


def build_risk_reasons(row, features, model):
    """
    Показывает не точные вероятности по причинам, а примерный вклад факторов в риск.
    Логика: берём важность фактора из модели и смотрим, насколько значение игры похоже
    на медиану мёртвых игр, а не живых.
    """
    if not hasattr(model, "feature_importances_"):
        return []

    importances = dict(zip(features, model.feature_importances_))
    reasons = []

    alive_part = df[pd.to_numeric(df.get("is_dead", pd.Series(dtype=float)), errors="coerce") == 0]
    dead_part = df[pd.to_numeric(df.get("is_dead", pd.Series(dtype=float)), errors="coerce") == 1]

    for feature in features:
        if feature not in df.columns or feature not in row.index:
            continue

        value = pd.to_numeric(pd.Series([row.get(feature)]), errors="coerce").iloc[0]
        if pd.isna(value):
            continue

        all_values = pd.to_numeric(df[feature], errors="coerce").dropna()
        alive_values = pd.to_numeric(alive_part.get(feature, pd.Series(dtype=float)), errors="coerce").dropna()
        dead_values = pd.to_numeric(dead_part.get(feature, pd.Series(dtype=float)), errors="coerce").dropna()

        if len(all_values) < 5 or len(alive_values) < 2 or len(dead_values) < 2:
            continue

        alive_median = alive_values.median()
        dead_median = dead_values.median()
        spread = all_values.quantile(0.75) - all_values.quantile(0.25)
        if pd.isna(spread) or spread == 0:
            spread = all_values.max() - all_values.min()
        if pd.isna(spread) or spread == 0:
            continue

        # Если значение ближе к медиане мёртвых игр, считаем это фактором риска.
        dist_alive = abs(value - alive_median)
        dist_dead = abs(value - dead_median)
        if dist_dead >= dist_alive:
            continue

        closeness = 1 - dist_dead / (dist_alive + dist_dead + 1e-9)
        score = float(importances.get(feature, 0)) * float(closeness)
        if score <= 0:
            continue

        if value > alive_median and dead_median > alive_median:
            direction = "выше, чем обычно у живых игр"
        elif value < alive_median and dead_median < alive_median:
            direction = "ниже, чем обычно у живых игр"
        else:
            direction = "ближе к типичным значениям мёртвых игр"

        reasons.append({
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "value": value,
            "score": score,
            "direction": direction,
        })

    reasons = sorted(reasons, key=lambda x: x["score"], reverse=True)[:5]
    total = sum(r["score"] for r in reasons) or 1
    for r in reasons:
        r["share"] = r["score"] / total
    return reasons


@app.callback(
    Output("prediction-result", "children"),
    Input("predict-game-search", "value"),
)
def update_prediction(steam_id):
    if steam_id is None:
        return ""

    if model_bundle is None:
        return html.Div(
            "Сначала запусти model.py, чтобы обучить модель. После этого появится файл models/mortality_model.joblib.",
            style={
                "padding": "12px 14px",
                "borderRadius": "12px",
                "background": "#fff4d6",
                "color": "#6a4a00",
                "fontWeight": "bold",
            },
        )

    row = alive_df[alive_df["steam_id"] == steam_id]
    if row.empty:
        return "Игра не найдена среди живых игр в таблице."

    row = row.iloc[0]
    model = model_bundle["model"]
    features = model_bundle["features"]

    x = pd.DataFrame([row])
    for feature in features:
        if feature not in x.columns:
            x[feature] = None
        x[feature] = pd.to_numeric(x[feature], errors="coerce")
        median_value = pd.to_numeric(df.get(feature, pd.Series(dtype=float)), errors="coerce").median()
        x[feature] = x[feature].fillna(median_value)

    x = x[features]
    probability = float(model.predict_proba(x)[0][1])
    verdict = "высокий риск смерти" if probability >= 0.65 else "средний риск" if probability >= 0.35 else "низкий риск"
    horizon = estimate_death_horizon(probability)
    reasons = build_risk_reasons(row, features, model)

    if probability >= 0.7:
        badge_color = DEAD_BLUE
    elif probability >= 0.4:
        badge_color = MID_BLUE
    else:
        badge_color = ALIVE_BLUE

    if reasons:
        reasons_block = html.Div(
            style={"marginTop": "12px"},
            children=[
                html.Div("Главные факторы риска:", style={"fontWeight": "bold", "color": DARK_BLUE}),
                html.Div(
                    style={"display": "grid", "gap": "6px", "marginTop": "7px"},
                    children=[
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "1fr 56px",
                                "gap": "8px",
                                "alignItems": "center",
                                "padding": "7px 9px",
                                "borderRadius": "9px",
                                "background": "white",
                                "border": f"1px solid {GRID}",
                            },
                            children=[
                                html.Div(r["label"], style={"fontSize": "14px"}),
                                html.Div(f"{r['share']:.0%}", style={"fontWeight": "bold", "color": DARK_BLUE, "textAlign": "right"}),
                            ],
                        )
                        for r in reasons[:4]
                    ],
                ),
            ],
        )
    else:
        reasons_block = html.Div(
            "Явных отдельных факторов риска нет.",
            style={"marginTop": "10px", "opacity": "0.8"},
        )

    return html.Div(
        style={
            "padding": "14px 16px",
            "borderRadius": "14px",
            "background": "#f1f7ff",
            "border": f"2px solid {badge_color}",
        },
        children=[
            html.Div(
                f"Прогноз модели: {verdict}",
                style={"fontWeight": "bold", "fontSize": "18px", "color": DARK_BLUE},
            ),
            html.Div(f"Риск низкого онлайна: {probability:.1%}", style={"marginTop": "6px"}),
            html.Div(f"Срок: {horizon}", style={"marginTop": "4px"}),
            reasons_block,
            html.Div(
                "Срок — грубая оценка, не точный прогноз.",
                style={"marginTop": "10px", "fontSize": "13px", "opacity": "0.72"},
            ),
        ],
    )


if __name__ == "__main__":
    app.run(debug=True)
