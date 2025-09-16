import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_operations(file_path: str) -> pd.DataFrame:
    """Читает Excel-файл с транзакциями"""
    try:
        df = pd.read_excel(file_path)
        logging.info(f"Файл {file_path} успешно загружен")
        return df
    except FileNotFoundError as e:
        logging.error(f"Файл не найден: {file_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"Ошибка при чтении {file_path}: {e}")
        raise


def parse_datetime(date_str: str | None) -> datetime:
    """
    Парсит строку формата 'YYYY-MM-DD HH:MM:SS'.
    Если дата не передана или пустая — возвращает текущую дату/время.
    """
    if not date_str:  # None, "", пустая строка
        now = datetime.now()
        logger.info("Дата не указана, используем текущую: %s", now)
        return now

    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        now = datetime.today()
        logger.warning("Некорректный формат даты '%s', используем текущую: %s", date_str, now.date())
        return now


def greeting_by_time(dt: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток:
    05:00-11:59 - Доброе утро
    12:00-16:59 - Добрый день
    17:00-21:59 - Добрый вечер
    23:00-04:59 - Доброй ночи
    """
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 17:
        return "Добрый день"
    if 17 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def group_card(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Группирует транзакции по последним 4 цифрам карты, вычисляет total_spent и cashback.
    Правило: считаем расходами транзакции, где 'Сумма платежа' < 0 (т.е. списания).
    В итоговом JSON total_spent — положительное число (сумма расходов по карте),
    cashback — total_spent / 100 (1 рубль на каждые 100 руб).
    """
    cards: Dict[str, float] = {}
    for t in transactions:
        card = str(t.get("Номер карты", "")).strip()
        # взять последние 4 символа ("*7197" -> "7197")
        last4 = card[-4:] if card else "0000"
        raw_amount = t.get("Сумма платежа", 0)
        try:
            amount = float(str(raw_amount).replace(",", "."))
        except Exception:
            # если не получилось, пропускаем транзакцию
            continue
        # считаем расходами только отрицательные значения
        if amount < 0:
            cards[last4] = cards.get(last4, 0.0) + abs(amount)

    result = []
    for last4, total_spent in cards.items():
        cashback = total_spent / 100.0  # 1 рубль на каждые 100 руб.
        result.append({"last_digits": last4, "total_spent": round(total_spent, 2), "cashback": round(cashback, 2)})
    return result


def top_transactions(transactions: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
    """
    Возвращает топ-N транзакций по сумме платежа (дата в формате дд.мм.гггг).
    - Некорректные суммы парсятся как 0.0 (функция не должна падать).
    - Даты любых форматов (Timestamp, datetime, строки с '.' или '-')
      приводятся к формату дд.мм.гггг.
    """
    prepared: list[dict[str, Any]] = []
    for t in transactions:
        # amount: некорректные форматы => 0.0
        raw_amount = t.get("Сумма платежа", 0)
        try:
            amount = float(str(raw_amount).replace(",", "."))
        except Exception:
            amount = 0.0

        # дата
        date_val = t.get("Дата операции", "")
        date_str = ""
        if isinstance(date_val, (pd.Timestamp, datetime)):
            date_str = date_val.strftime("%d.%m.%Y")
        elif isinstance(date_val, str):
            if "." in date_val:
                try:
                    date_str = pd.to_datetime(date_val, dayfirst=True, errors="raise").strftime("%d.%m.%Y")
                except Exception:
                    date_str = date_val.split(" ")[0]
            else:
                # строки без точки → стандартный ISO-формат (2021-12-01 и т.п.)
                try:
                    date_str = pd.to_datetime(date_val, errors="raise").strftime("%d.%m.%Y")
                except Exception:
                    date_str = date_val.split(" ")[0]
        else:
            date_str = ""

        prepared.append(
            {
                "date": date_str,
                "amount": abs(amount),
                "category": t.get("Категория", "") or "",
                "description": t.get("Описание", "") or "",
            }
        )

    # Сортируем по модулю суммы (убывание) и берём top_n
    top = sorted(prepared, key=lambda x: abs(x["amount"]), reverse=True)[:top_n]
    return top


# чтение пользовательских настроек
def read_user_settings(path: str = "user_settings.json") -> Dict[str, Any]:
    """
    Читает пользовательские настройки (валюты, акции)
    Если файл отсутствует или JSON некорректный — возвращает значения по умолчанию.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        full_path = os.path.join(base_dir, path)

        with open(full_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except FileNotFoundError:
        logger.warning(f"Файл user_settings.json не найден, загружаем значения по умолчанию: {path}")
        return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "MSFT"]}
