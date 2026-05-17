# Why Games Die — Analysis

## Состав группы
Бокатенко Вадим (Gemoskorp), Федусенко Илья (fedusenkoilya-dev)

## Идея проекта
Анализируем данные по играм и ищем "мёртвые".
Изучаем что послужило причиной, как быстро игры
умирают и могут ли возродиться.

## Источники данных
- SteamDB — история онлайна (Playwright)
- Steam API — данные по играм
- Metacritic — оценки критиков и пользователей
- Steam Reviews — динамика отзывов
- IGDB — жанры, режимы игры
- HowLongToBeat — время прохождения игр

## Структура проекта
parsers/     — парсеры всех источников
processing/  — обработка и объединение данных
analysis/    — модель предсказания смерти игры
dashboard/   — интерактивный дэшборд

## Как запустить
pip install -r requirements.txt
python scripts/get_game_ids.py
python scripts/run_pipeline.py
python dashboard/app.py
