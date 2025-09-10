from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest

from src.external_api import convert_currency, get_stock_price


@pytest.mark.parametrize(
    "mock_result, expected",
    [
        ({"result": 123.45}, 123.45),  # успешный ответ
        ({}, None),  # пустой результат
    ],
)
def test_convert_currency_success(mock_result: Dict[str, Any], expected: Optional[float]) -> None:
    """
    Тестирует convert_currency при успешном ответе API.
    Проверяются оба сценария:
      - корректный результат (есть поле "result"),
      - пустой словарь (функция вернёт None).
    """
    with patch("src.external_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_result
        mock_get.return_value = mock_response

        result = convert_currency(100.0, "USD", "EUR")
        assert result == expected


def test_convert_currency_error(caplog: pytest.LogCaptureFixture) -> None:
    """
    Тестирует convert_currency при ошибке запроса.
    Проверяет, что функция возвращает None и логирует ошибку.
    """
    with patch("src.external_api.requests.get", side_effect=Exception("API error")):
        result = convert_currency(100.0, "USD", "EUR")
        assert result is None
        assert "Ошибка при конвертации валюты" in caplog.text


@pytest.mark.parametrize(
    "mock_result, expected",
    [
        ({"Global Quote": {"05. price": "150.55"}}, 150.55),  # успешный ответ
        ({}, None),  # нет ключа "Global Quote"
    ],
)
def test_get_stock_price_success_and_key_error(mock_result: Dict[str, Any], expected: Optional[float]) -> None:
    """
    Тестирует get_stock_price при успешном и некорректном ответе API.
    Сценарии: - корректный JSON с ценой,
              - отсутствует ключ "Global Quote" → KeyError → функция возвращает None.
    """
    with patch("src.external_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_result
        mock_get.return_value = mock_response

        result = get_stock_price("AAPL")
        assert result == expected


def test_get_stock_price_error(caplog: pytest.LogCaptureFixture) -> None:
    """
    Тестирует get_stock_price при ошибке запроса (raise_for_status выбрасывает Exception).
    Проверяет, что функция возвращает None и логирует ошибку.
    """
    with patch("src.external_api.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API error")
        mock_get.return_value = mock_response

        result = get_stock_price("AAPL")
        assert result is None
        assert "Ошибка при получении цены акции" in caplog.text
