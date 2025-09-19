import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Hashable, Optional, TypeVar, cast

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_date(date_str: str | None) -> datetime | None:
    """Парсинг даты с проверкой формата DD.MM.YYYY"""
    if not date_str:
        logging.error("Введите дату в формате DD.MM.YYYY")
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        logging.error("Неверный формат даты. Введите дату в формате DD.MM.YYYY")
        return None


F = TypeVar("F", bound=Callable[..., Any])


def save_report(func: F) -> F:
    """
    Декоратор: сохраняет результат функции в JSON файл.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        filename = f"{func.__name__}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            logging.info(f"Отчет сохранен в файл {filename}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении отчета: {e}")

        return result

    return cast(F, wrapper)


@save_report
def spending_by_category(transactions: pd.DataFrame, category: str, date_str: str) -> Optional[dict[str, Any]]:
    """Формирует отчет по заданной категории за последние 3 месяца."""
    end_date = parse_date(date_str)
    if not end_date:
        return None

    start_date = end_date - pd.DateOffset(months=3)
    logging.info(f"Формируем отчет по категории '{category}' за период {start_date.date()} - {end_date.date()}")

    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], errors="coerce", dayfirst=True)

    # приведение к нижнему регистру
    transactions["Категория"] = transactions["Категория"].apply(lambda x: str(x).lower())
    category = category.lower()

    df_filtered = transactions[
        (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Категория"] == category)
    ].copy()

    amounts: pd.Series[float] = df_filtered["Сумма платежа"].apply(lambda x: abs(float(str(x).replace(",", "."))))
    total_spent: float = float(amounts.sum())

    return {
        "category": category,
        "period": f"{start_date.date()} - {end_date.date()}",
        "total_spent": round(total_spent, 2),
    }


@save_report
def spending_by_weekday(transactions: pd.DataFrame, date_str: str) -> Optional[list[dict[Hashable, Any]]]:
    """Формирует отчет по дням недели за последние 3 месяца."""
    end_date = parse_date(date_str)
    if not end_date:
        return None

    start_date = end_date - pd.DateOffset(months=3)
    logging.info(f"Формируем отчет по дням недели за период {start_date.date()} - {end_date.date()}")

    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], errors="coerce", dayfirst=True)

    df_filtered = transactions[
        (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
    ].copy()

    df_filtered["weekday"] = df_filtered["Дата операции"].dt.day_name()

    # Правильная агрегация
    grouped = df_filtered.groupby("weekday")["Сумма платежа"]
    sums: pd.Series[float] = pd.to_numeric(grouped.apply(lambda s: s.astype(float).abs().sum()), errors="coerce")
    sums = sums.round(2)

    result: list[dict[Hashable, Any]] = sums.reset_index().to_dict(orient="records")

    logging.info("Отчет по дням недели успешно сформирован")
    return result
