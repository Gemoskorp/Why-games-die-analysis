from howlongtobeatpy import HowLongToBeat
import pandas as pd
import os
from datetime import datetime
import time

def get_hltb_data(game_names, save_csv=True, output_dir="data/raw/hltb", delay=1.5):
 
    results = []
    hltb = HowLongToBeat()
    total = len(game_names)
    found_count = 0
    not_found_count = 0
    

    print(f"Начинаем парсинг {total} игр")
    print(f"Задержка между запросами: {delay} сек")

    
    # Создаём папку для сохранения промежуточных результатов
    os.makedirs(output_dir, exist_ok=True)
    
    for i, game_name in enumerate(game_names, 1):
        print(f"\n[{i}/{total}] Ищу: {game_name}")
        
        try:
            # Поиск игры
            search_results = hltb.search(game_name)
            
            if search_results and len(search_results) > 0:
                # Находим наиболее похожий результат
                best_game = max(search_results, key=lambda x: x.similarity)
                
                # Собираем все доступные данные
                game_data = {
                    'name': game_name,
                    'hltb_id': getattr(best_game, 'id', None),
                    'hltb_main': getattr(best_game, 'main_story', None),
                    'hltb_extra': getattr(best_game, 'main_plus_sides', None),
                    'hltb_complete': getattr(best_game, 'completionist', None),
                    'similarity': best_game.similarity,
                    'game_name_found': getattr(best_game, 'game_name', ''),
                    'release_year': getattr(best_game, 'release_year', None),
                    'platform': getattr(best_game, 'platform', ''),
                }
                
                results.append(game_data)
                found_count += 1
                
                print(f"  ✓ Найдено: {game_data['game_name_found']}")
                print(f"    Похожесть: {game_data['similarity']:.2f}")
                print(f"    Основная сюжетная линия: {game_data['hltb_main']} ч")
                if game_data['hltb_extra']:
                    print(f"    Сюжет + дополнения: {game_data['hltb_extra']} ч")
                if game_data['hltb_complete']:
                    print(f"    Полное прохождение: {game_data['hltb_complete']} ч")
            else:
                print(f"  ✗ Не найдено: {game_name}")
                results.append({
                    'name': game_name,
                    'hltb_id': None,
                    'hltb_main': None,
                    'hltb_extra': None,
                    'hltb_complete': None,
                    'similarity': 0,
                    'game_name_found': '',
                    'release_year': None,
                    'platform': '',
                })
                not_found_count += 1
                
        except Exception as e:
            print(f"  ✗ Ошибка при поиске {game_name}: {e}")
            results.append({
                'name': game_name,
                'hltb_id': None,
                'hltb_main': None,
                'hltb_extra': None,
                'hltb_complete': None,
                'similarity': 0,
                'game_name_found': '',
                'release_year': None,
                'platform': '',
                'error': str(e),
            })
            not_found_count += 1
        
        # Сохраняем промежуточные результаты каждые 50 игр
        if i % 50 == 0:
            temp_df = pd.DataFrame(results)
            temp_path = os.path.join(output_dir, f"hltb_games_partial_{i}.csv")
            temp_df.to_csv(temp_path, index=False, encoding='utf-8-sig')
            print(f"\n  [Промежуточное сохранение] {i}/{total} игр сохранено в {temp_path}")
            print(f"  Найдено: {found_count}, Не найдено: {not_found_count}")
        
        # Задержка между запросами
        time.sleep(delay)
    
    # Создаём итоговый DataFrame
    df = pd.DataFrame(results)
    
    # Сохраняем в CSV если нужно
    if save_csv:
        # Формируем имя файла с датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hltb_games_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Сохраняем
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print("\n" + "=" * 60)
        print(f"ИТОГОВОЕ СОХРАНЕНИЕ")
        print("=" * 60)
        print(f"Файл: {filepath}")
        print(f"Всего игр в файле: {len(df)}")
        print(f"Успешно найдено: {found_count}")
        print(f"Не найдено: {not_found_count}")
        print(f"Процент найденных: {found_count/len(df)*100:.1f}%")
        print("=" * 60)
    
    return df


def load_game_names_from_csv(csv_path, name_column='name'):
    
    try:
        df = pd.read_csv(csv_path)
        game_names = df[name_column].tolist()
        print(f"Загружено {len(game_names)} названий игр из {csv_path}")
        print(f"Первые 5 названий: {game_names[:5]}")
        return game_names
    except FileNotFoundError:
        print(f"Файл {csv_path} не найден!")
        return []
    except KeyError:
        print(f"Колонка '{name_column}' не найдена в файле!")
        print(f"Доступные колонки: {df.columns.tolist()}")
        return []


def resume_parsing_from_partial(partial_file, output_dir="data/raw/hltb"):
  
    # Загружаем уже обработанные игры
    done_df = pd.read_csv(partial_file)
    done_names = set(done_df['name'].tolist())
    
    # Загружаем полный список
    full_names = load_game_names_from_csv("data/game_ids.csv")
    
    # Находим оставшиеся игры
    remaining_names = [n for n in full_names if n not in done_names]
    
    print(f"Уже обработано: {len(done_names)}")
    print(f"Осталось: {len(remaining_names)}")
    
    if remaining_names:
        # Продолжаем парсинг
        new_df = get_hltb_data(remaining_names, save_csv=True, output_dir=output_dir)
        
        # Объединяем с уже имеющимися данными
        final_df = pd.concat([done_df, new_df], ignore_index=True)
        
        # Сохраняем полный результат
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = os.path.join(output_dir, f"hltb_games_complete_{timestamp}.csv")
        final_df.to_csv(final_path, index=False, encoding='utf-8-sig')
        print(f"\nПолные данные сохранены в: {final_path}")
        
        return final_df
    else:
        print("Все игры уже обработаны!")
        return done_df



if __name__ == "__main__":

    print("ПАРСИНГ HOWLONGTOBEAT ДЛЯ 750 ИГР")

    
    # Загружаем названия игр из CSV файла
    game_names = load_game_names_from_csv("data/game_ids.csv", name_column='name')
    
    if not game_names:
        print("\nНе удалось загрузить названия игр. Проверьте путь к файлу.")
        print("Ожидаемый путь: data/game_ids.csv")
    else:
        # Запускаем парсинг всех игр
        df_hltb = get_hltb_data(
            game_names, 
            save_csv=True, 
            output_dir="data/raw/hltb",
            delay=1.5  # Задержка между запросами (секунды)
        )
        
        # Показываем краткую статистику
        
        # Статистика по времени прохождения
        print("\nСтатистика по времени прохождения (найденные игры):")
        print(f"  Минимальное время (main): {df_hltb['hltb_main'].min():.1f} ч")
        print(f"  Максимальное время (main): {df_hltb['hltb_main'].max():.1f} ч")
        print(f"  Среднее время (main): {df_hltb['hltb_main'].mean():.1f} ч")
        print(f"  Медианное время (main): {df_hltb['hltb_main'].median():.1f} ч")
