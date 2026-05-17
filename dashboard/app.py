import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json

app = dash.Dash(__name__)

# загружаем датасет
df = pd.read_csv("data/processed/games_dataset.csv")

app.layout = html.Div([
    html.H1("Почему умирают игры", style={"textAlign": "center"}),

    # фильтры
    html.Div([
        html.Label("Жанр:"),
        dcc.Dropdown(
            id="genre-filter",
            options=[{"label": g, "value": g} for g in df["genres"].dropna().unique()],
            multi=True,
            placeholder="Все жанры"
        ),
        html.Label("Статус:"),
        dcc.RadioItems(
            id="status-filter",
            options=[
                {"label": "Все",      "value": "all"},
                {"label": "Живые",    "value": "alive"},
                {"label": "Мёртвые",  "value": "dead"},
            ],
            value="all",
            inline=True
        ),
    ], style={"width": "50%", "margin": "auto"}),

    # scatter: пиковый онлайн vs metascore
    dcc.Graph(id="scatter-plot"),

    # поиск конкретной игры и её график онлайна
    html.Div([
        html.Label("Найти игру:"),
        dcc.Dropdown(
            id="game-search",
            options=[{"label": row["name"], "value": row["steam_id"]}
                     for _, row in df.iterrows()],
            placeholder="Введи название игры..."
        ),
    ], style={"width": "50%", "margin": "20px auto"}),

    dcc.Graph(id="online-history-plot"),

    # топ факторов
    dcc.Graph(id="feature-importance-plot"),
])


@app.callback(
    Output("scatter-plot", "figure"),
    Input("genre-filter", "value"),
    Input("status-filter", "value"),
)
def update_scatter(genres, status):
    filtered = df.copy()
    if genres:
        filtered = filtered[filtered["genres"].isin(genres)]
    if status == "alive":
        filtered = filtered[filtered["is_dead"] == 0]
    elif status == "dead":
        filtered = filtered[filtered["is_dead"] == 1]

    fig = px.scatter(
        filtered,
        x="metascore",
        y="peak_all_time",
        color=filtered["is_dead"].map({0: "Живая", 1: "Мёртвая"}),
        hover_name="name",
        title="Пиковый онлайн vs Metascore",
        labels={"metascore": "Metascore", "peak_all_time": "Пиковый онлайн"},
        color_discrete_map={"Живая": "green", "Мёртвая": "red"},
    )
    return fig


@app.callback(
    Output("online-history-plot", "figure"),
    Input("game-search", "value"),
)
def update_online_history(steam_id):
    if not steam_id:
        return go.Figure()

    row = df[df["steam_id"] == steam_id].iloc[0]
    history = json.loads(row["online_history"])

    months = [h["month"] for h in history]
    avg_online = [h["avg_online"] for h in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=avg_online,
        mode="lines+markers",
        name="Средний онлайн"
    ))

    # отмечаем момент смерти
    if row.get("months_to_death"):
        death_month = months[int(row["months_to_death"])]
        fig.add_vline(
            x=death_month,
            line_dash="dash",
            line_color="red",
            annotation_text="Момент смерти"
        )

    fig.update_layout(
        title=f"История онлайна: {row['name']}",
        xaxis_title="Месяц",
        yaxis_title="Средний онлайн",
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)