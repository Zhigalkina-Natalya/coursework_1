import logging
from typing import Any, Dict, Hashable

import pandas as pd

from src.external_api import convert_currency, get_stock_price
from src.utils import (
    greeting_by_time,
    group_card,
    parse_datetime,
    read_operations,
    read_user_settings,
    top_transactions,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_main_page(date_str: str, transactions: list[dict[Hashable, Any]]) -> dict[str, Any]:
    """
    Чистая бизнес-логика: принимает дату и список транзакций, возвращает JSON-ответ.
    """
    dt = parse_datetime(date_str)
    greeting = greeting_by_time(dt)

    # диапазон дат
    month_start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    logger.info("Фильтрация транзакций за период: %s - %s", month_start, dt)

    # фильтруем транзакции
    df = pd.DataFrame(transactions)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    mask = (df["Дата операции"] >= month_start) & (df["Дата операции"] <= dt)
    filtered = df[mask]

    filtered_transactions = filtered.to_dict(orient="records")

    # расходы по картам
    cards_info = group_card(filtered_transactions)

    # топ 5 транзакций
    top_ops = top_transactions(filtered_transactions, top_n=5)

    # пользовательские настройки
    settings = read_user_settings()

    # курсы валют
    currencies = []
    for cur in settings.get("user_currencies", []):
        rate = convert_currency(1, cur, "RUB")
        currencies.append({"currency": cur, "rate": rate})

    # акции
    stocks = []
    for symbol in settings.get("user_stocks", []):
        price = get_stock_price(symbol)
        stocks.append({"stock": symbol, "price": price})

    return {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_ops,
        "currency_rates": currencies,
        "stock_prices": stocks,
    }


def get_main_page(date_str: str) -> Dict[str, Any]:
    """
    Главная функция для веб-страницы.
    Принимает строку даты-времени, загружает транзакции и вызывает бизнес-логику.
    """
    df = read_operations("data/operations.xlsx")
    transactions = df.to_dict(orient="records")
    return process_main_page(date_str, transactions)


if __name__ == "__main__":
    result = get_main_page("2021-12-21 15:30:00")
    print(result)
