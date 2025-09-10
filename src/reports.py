import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Hashable, TypeVar, cast

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
def spending_by_category(transactions: pd.DataFrame, category: str, date_str: str) -> Dict[str, Any]:
    """
    Отчет по заданной категории за последние 3 месяца.
    """
    end_date = datetime.strptime(date_str, "%d.%m.%Y")
    start_date = end_date - pd.DateOffset(months=3)

    logging.info(f"Формируем отчет по категории '{category}' " f"за период {start_date.date()} - {end_date.date()}")

    df_filtered = transactions[
        (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Категория"] == category)
    ].copy()

    total_spent = df_filtered["Сумма операции"].apply(lambda x: abs(x)).sum()

    logging.info(f"Общая сумма расходов по категории '{category}': {total_spent}")

    return {"category": category, "period": f"{start_date.date()} - {end_date.date()}", "total_spent": total_spent}


@save_report
def spending_by_weekday(transactions: pd.DataFrame, date_str: str) -> list[dict[Hashable, Any]]:
    """
    Отчет по дням недели за последние 3 месяца.
    """
    end_date = datetime.strptime(date_str, "%d.%m.%Y")
    start_date = end_date - pd.DateOffset(months=3)

    logging.info(f"Формируем отчет по дням недели " f"за период {start_date.date()} - {end_date.date()}")

    df_filtered = transactions[
        (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
    ].copy()

    df_filtered["weekday"] = df_filtered["Дата операции"].dt.day_name()

    result = (
        df_filtered.groupby("weekday")["Сумма операции"]
        .apply(lambda x: abs(x).sum())
        .reset_index()
        .to_dict(orient="records")
    )

    logging.info("Отчет по дням недели успешно сформирован")

    return result
