import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd

class BaseParser(ABC):
    def __init__(self, output_dir: str, delay: float = 1.5):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def parse_game(self, game_id: str | int) -> dict:
        """Парсит одну игру, возвращает словарь с данными"""
        pass

    def parse_all(self, game_ids: list) -> pd.DataFrame:
        results = []
        for i, game_id in enumerate(game_ids):
            try:
                self.logger.info(f"[{i+1}/{len(game_ids)}] Парсим {game_id}")
                data = self.parse_game(game_id)
                if data:
                    results.append(data)
            except Exception as e:
                self.logger.error(f"Ошибка при парсинге {game_id}: {e}")
            time.sleep(self.delay)
        df = pd.DataFrame(results)
        self._save(df)
        return df

    def _save(self, df: pd.DataFrame):
        path = self.output_dir / f"{self.__class__.__name__}_raw.csv"
        df.to_csv(path, index=False)
        self.logger.info(f"Сохранено: {path}")