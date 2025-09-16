import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.services import find_personal_transfers, profitable_cashback_categories

# ТЕСТЫ profitable_cashback_categories


def test_profitable_cashback_categories_success() -> None:
    """Тест успешного расчета кешбэка по категориям за январь 2023 года."""
    test_transactions: List[Dict[str, Any]] = [
        {
            "Дата операции": "15.01.2023 12:30:45",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": "50.0",
        },
        {
            "Дата операции": "20.01.2023 15:45:22",
            "Категория": "Супермаркеты",
            "Бонусы (включая кэшбэк)": "75.5",
        },
        {
            "Дата операции": "10.01.2023 18:20:11",
            "Категория": "Переводы",
            "Бонусы (включая кэшбэк)": "0",
        },
    ]

    result: str = profitable_cashback_categories(test_transactions, 2023, 1)
    result_data: Dict[str, float] = json.loads(result)

    expected: Dict[str, float] = {"Супермаркеты": 125.5, "Переводы": 0.0}
    assert result_data == expected


def test_profitable_cashback_categories_no_data() -> None:
    """Тест обработки случая, когда нет данных за указанный период."""
    result = profitable_cashback_categories([], 2024, 1)
    result_data = json.loads(result)
    assert result_data == {}


@pytest.mark.parametrize(
    "year, month",
    [
        (2025, 13),  # невалидный месяц
        (2025, 0),  # месяц меньше 1
        ("not_a_year", 5),  # невалидный год
    ],
)
def test_profitable_cashback_categories_invalid(
    sample_transactions: list[dict[str, Any]], year: int, month: int
) -> None:
    result = profitable_cashback_categories(sample_transactions, year, month)
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_profitable_cashback_categories_none_cashback() -> None:
    data = [{"Дата операции": "01.01.2024", "Категория": "Тест", "Бонусы (включая кэшбэк)": ""}]
    result = profitable_cashback_categories(data, 2024, 1)
    parsed = json.loads(result)
    assert parsed == {}  # теперь сравниваем словари, а не строки


def test_profitable_cashback_categories_empty_cashback() -> None:
    """Тест обработки пустой строки в поле бонусов."""
    data = [{"Дата операции": "15.01.2023 12:30:45", "Категория": "Тест", "Бонусы (включая кэшбэк)": ""}]
    result = profitable_cashback_categories(data, 2023, 1)
    result_data = json.loads(result)
    assert result_data == {"Тест": 0.0}


def test_profitable_cashback_categories_empty_data() -> None:
    """Пустой список транзакций -> {}"""
    result = profitable_cashback_categories([], 2024, 1)
    assert json.loads(result) == {}


def test_profitable_cashback_categories_invalid_date_format() -> None:
    """Транзакции с некорректной датой не должны падать"""
    data = [{"Дата операции": "invalid_date", "Категория": "Еда", "Бонусы (включая кэшбэк)": "10"}]
    result = profitable_cashback_categories(data, 2024, 1)
    parsed = json.loads(result)
    # кешбэк не учитывается
    assert parsed == {}


def test_profitable_cashback_categories_valid_with_cashback() -> None:
    """Корректный расчет кешбэка"""
    data = [
        {"Дата операции": "10.01.2024 12:00:00", "Категория": "Еда", "Бонусы (включая кэшбэк)": "10"},
        {"Дата операции": "15.01.2024 15:30:00", "Категория": "Еда", "Бонусы (включая кэшбэк)": "20"},
    ]
    result = profitable_cashback_categories(data, 2024, 1)
    parsed = json.loads(result)
    assert parsed == {"Еда": 30.0}


def test_profitable_cashback_categories_invalid_cashback_value() -> None:
    """Некорректное значение кешбэка не должно ломать расчет"""
    data = [{"Дата операции": "10.01.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": "abc"}]
    result = profitable_cashback_categories(data, 2024, 1)
    parsed = json.loads(result)
    assert parsed == {}


def test_profitable_cashback_categories_logs_error() -> None:
    """Проверка, что при ошибке парсинга даты логируется ошибка"""
    bad_data = [{"Дата операции": "неправильная дата", "Категория": "Еда", "Бонусы (включая кэшбэк)": "10"}]

    with patch("src.services.logging.Logger.error") as mock_logger_error:
        result = profitable_cashback_categories(bad_data, 2024, 1)
        parsed = json.loads(result)
        # функция возвращает пустой JSON при ошибке
        assert parsed == {}
        # проверяем, что logger.error был вызван
        mock_logger_error.assert_called()


# ТЕСТЫ find_personal_transfers


def test_find_personal_transfers_success() -> None:
    """Тест успешного поиска переводов физическим лицам."""
    transactions: List[Dict[str, Any]] = [
        {"Дата операции": "10.01.2023 18:20:11", "Категория": "Переводы", "Описание": "Иван П."},
        {"Дата операции": "25.01.2023 14:10:05", "Категория": "Переводы", "Описание": "Мария С."},
        {"Дата операции": "15.01.2023 12:30:45", "Категория": "Супермаркеты", "Описание": "Покупка"},
    ]

    result: str = find_personal_transfers(transactions)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert len(result_data) == 2
    assert all(t["Категория"] == "Переводы" for t in result_data)
    assert all("." in t["Описание"] for t in result_data)


def test_find_personal_transfers_no_matches(sample_transactions: list[dict[str, Any]]) -> None:
    """Тест поиска переводов, когда нет подходящих данных."""
    no_transfers: List[Dict[str, Any]] = [t for t in sample_transactions if t["Категория"] != "Переводы"]

    result = find_personal_transfers(no_transfers)
    result_data = json.loads(result)
    assert result_data == []


def test_find_personal_transfers_empty() -> None:
    """Тест поиска переводов в пустом списке транзакций."""
    result = find_personal_transfers([])
    result_data = json.loads(result)
    assert result_data == []


def test_personal_transfers_wrong_format() -> None:
    """Тест поиска переводов с некорректным форматом имени."""
    data = [{"Категория": "Переводы", "Описание": "Иван Петров"}]  # нет точки
    result = find_personal_transfers(data)
    result_data = json.loads(result)
    assert result_data == []


def test_find_personal_transfers_valid_case() -> None:
    """Поиск переводов физлицам с корректным описанием"""
    transactions = [
        {"Дата операции": "01.01.2024", "Категория": "Переводы", "Описание": "Иван П."},
        {"Дата операции": "02.01.2024", "Категория": "Еда", "Описание": "Магазин"},  # лишнее
    ]
    result = find_personal_transfers(transactions)
    parsed = json.loads(result)
    assert len(parsed) == 1
    assert parsed[0]["Описание"] == "Иван П."


def test_find_personal_transfers_invalid_description() -> None:
    """Описание без фамилии с точкой не считается переводом"""
    transactions = [
        {"Дата операции": "01.01.2024", "Категория": "Переводы", "Описание": "Иван Иванов"},
    ]
    result = find_personal_transfers(transactions)
    parsed = json.loads(result)
    assert parsed == []


def test_find_personal_transfers_empty_list() -> None:
    """Пустой список транзакций"""
    result = find_personal_transfers([])
    parsed = json.loads(result)
    assert parsed == []


def test_find_personal_transfers_logs_error() -> None:
    """Если описание None — функция возвращает пустой список, лог не вызывается"""
    bad_data = [{"Категория": "Переводы", "Описание": None}]
    result = find_personal_transfers(bad_data)
    parsed = json.loads(result)
    assert parsed == []
