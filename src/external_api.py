import logging
import os
from typing import Dict, Union

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# загрузка переменных окружения из .env
load_dotenv()

CURRENCY_API_URL = os.getenv("CURRENCY_API_URL")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

STOCKS_API_URL = os.getenv("STOCKS_API_URL")
STOCKS_API_KEY = os.getenv("STOCKS_API_KEY")


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float | None:
    """
    Конвертация валюты через apilayer
    Args:
        amount (float): сумма для конвертации
        from_currency (str): код исходной валюты (например, "USD")
        to_currency (str): код целевой валюты (например, "RUB")

    Returns:
        float | None: результат конвертации или None в случае ошибки
    """
    headers = {"apikey": CURRENCY_API_KEY}
    params: Dict[str, Union[str, int, float]] = {"from": from_currency, "to": to_currency, "amount": amount}
    if not CURRENCY_API_URL:
        logger.error("Не задан CURRENCY_API_URL в .env")
        return None
    try:
        response = requests.get(CURRENCY_API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        result = data.get("result")
        if isinstance(result, (int, float)):
            return float(result)
        return None
    except Exception as e:
        logger.error("Ошибка при конвертации валюты: %s", e)
        return None


def get_stock_price(symbol: str) -> float | None:
    """Получить цену акции через API - Alpha Vantage"""
    if not STOCKS_API_URL or not STOCKS_API_KEY:
        logger.error("Не задан STOCKS_API_URL в .env")
        return None
    try:
        params: Dict[str, Union[str, int, float]] = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": STOCKS_API_KEY,
        }
        response = requests.get(STOCKS_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return float(data["Global Quote"]["05. price"])
    except Exception as e:
        logger.error("Ошибка при получении цены акции %s: %s", symbol, e)
        return None
