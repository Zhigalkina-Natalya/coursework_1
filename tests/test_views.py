import json
from typing import Any, Dict, List
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import get_main_page, process_main_page


def test_process_main_page_basic(sample_transactions: List[Dict[str, Any]]) -> None:
    """Тест проверяем бизнес-логику без чтения файлов и вызова реального API."""
    # Мокаем API и настройки
    with (
        patch("src.views.convert_currency", return_value=100.0),
        patch("src.views.get_stock_price", return_value=500.0),
        patch("src.views.read_user_settings", return_value={"user_currencies": ["USD"], "user_stocks": ["AAPL"]}),
    ):
        date_str = "2025-09-15 12:00:00"
        result: Dict[str, Any] = process_main_page(date_str, sample_transactions)

        # Проверяем ключи
        assert set(result.keys()) == {"greeting", "cards", "top_transactions", "currency_rates", "stock_prices"}
        assert result["greeting"] == "Добрый день"
        assert all("last_digits" in card for card in result["cards"])
        assert all("amount" in t for t in result["top_transactions"])
        assert result["currency_rates"] == [{"currency": "USD", "rate": 100.0}]
        assert result["stock_prices"] == [{"stock": "AAPL", "price": 500.0}]


def test_get_main_page_calls_process_main_page(sample_transactions: List[Dict[str, Any]]) -> None:
    """
    Tест проверяет интеграцию функций views: читается файл (мокается), передаются транзакции, вызывается бизнес-логика.
    """
    # Конвертируем list в DataFrame, чтобы read_operations возвращал DataFrame
    df_mock = pd.DataFrame(sample_transactions)
    with (
        patch("src.views.read_operations", return_value=df_mock),
        patch("src.views.process_main_page") as mock_process,
    ):
        mock_process.return_value = {"mock": True}
        result_json: str = get_main_page("2025-09-15 12:00:00")

        mock_process.assert_called_once()
        result: Dict[str, Any] = json.loads(result_json)
        assert result == {"mock": True}


@pytest.mark.parametrize(
    "hour, expected_greeting",
    [
        (7, "Доброе утро"),
        (13, "Добрый день"),
        (18, "Добрый вечер"),
        (23, "Доброй ночи"),
    ],
)
def test_greeting_in_process_main_page(
    sample_transactions: List[Dict[str, Any]], hour: int, expected_greeting: str
) -> None:
    date_str = f"2025-09-15 {hour}:00:00"
    with (
        patch("src.views.convert_currency", return_value=1.0),
        patch("src.views.get_stock_price", return_value=1.0),
        patch("src.views.read_user_settings", return_value={"user_currencies": [], "user_stocks": []}),
    ):
        result: Dict[str, Any] = process_main_page(date_str, sample_transactions)
        assert result["greeting"] == expected_greeting
