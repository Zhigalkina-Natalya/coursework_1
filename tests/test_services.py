import json
from typing import Any, Dict, List

from src.services import find_personal_transfers, profitable_cashback_categories

# from unittest.mock import patch


test_transactions: List[Dict[str, Any]] = [
    {
        "Дата операции": "15.01.2023 12:30:45",
        "Категория": "Супермаркеты",
        "Кэшбэк": "50.0",
        "Описание": "Покупка в Пятёрочке",
    },
    {
        "Дата операции": "20.01.2023 15:45:22",
        "Категория": "Супермаркеты",
        "Кэшбэк": "75.5",
        "Описание": "Покупка в Магните",
    },
    {"Дата операции": "05.02.2023 09:15:33", "Категория": "АЗС", "Кэшбэк": "30.0", "Описание": "Заправка Лукойл"},
    {"Дата операции": "10.01.2023 18:20:11", "Категория": "Переводы", "Кэшбэк": "0", "Описание": "Иван П."},
    {"Дата операции": "25.01.2023 14:10:05", "Категория": "Переводы", "Кэшбэк": "0", "Описание": "Мария С."},
]


def test_profitable_cashback_categories_success() -> None:
    """Тест успешного расчета кешбэка по категориям за январь 2023 года."""
    result: str = profitable_cashback_categories(test_transactions, 2023, 1)
    result_data: Dict[str, float] = json.loads(result)

    expected: Dict[str, float] = {"Супермаркеты": 125.5, "Переводы": 0.0}
    assert result_data == expected


def test_profitable_cashback_categories_no_data() -> None:
    """Тест обработки случая, когда нет данных за указанный период."""
    result = profitable_cashback_categories(test_transactions, 2024, 1)
    result_data = json.loads(result)

    assert result_data == {}


def test_profitable_cashback_categories_empty() -> None:
    """Тест обработки пустого списка транзакций."""
    result = profitable_cashback_categories([], 2023, 1)
    result_data = json.loads(result)

    assert result_data == {}


def test_profitable_cashback_categories_exception_handling() -> None:
    """Тест обработки исключений в profitable_cashback_categories."""
    # Данные, которые вызовут исключение при парсинге даты
    problematic_data: list = [{"Дата операции": "invalid_date"}]

    result: str = profitable_cashback_categories(problematic_data, 2023, 1)
    result_data: dict = json.loads(result)

    assert "error" in result_data


def test_find_personal_transfers_exception_handling() -> None:
    """Тест обработки исключений в find_personal_transfers."""
    # Данные, которые могут вызвать исключение в регулярном выражении
    problematic_data = [{"Описание": None, "Категория": "Переводы"}]

    result = find_personal_transfers(problematic_data)
    result_data = json.loads(result)

    assert result_data == []


def test_profitable_cashback_categories_bad_date() -> None:
    """Тест обработки некорректного формата даты в транзакциях."""
    bad_data: List[Dict[str, Any]] = [{"Дата операции": "неправильная дата", "Категория": "Тест", "Кэшбэк": "10"}]

    result: str = profitable_cashback_categories(bad_data, 2023, 1)
    result_data: Dict[str, Any] = json.loads(result)

    assert "error" in result_data


def test_profitable_cashback_categories_no_category() -> None:
    """Тест обработки транзакций без указания категории."""
    data: List[Dict[str, Any]] = [{"Дата операции": "15.01.2023 12:30:45", "Кэшбэк": "10.0"}]

    result: str = profitable_cashback_categories(data, 2023, 1)
    result_data: Dict[str, float] = json.loads(result)

    assert result_data == {"Другое": 10.0}


def test_profitable_cashback_categories_none_cashback() -> None:
    """Тест обработки значения None в поле Кэшбэк."""
    data: List[Dict[str, Any]] = [{"Дата операции": "15.01.2023 12:30:45", "Категория": "Тест", "Кэшбэк": None}]

    result: str = profitable_cashback_categories(data, 2023, 1)
    result_data: Dict[str, float] = json.loads(result)

    assert result_data == {"Тест": 0.0}


def test_profitable_cashback_categories_empty_cashback() -> None:
    """Тест обработки пустой строки в поле Кэшбэк."""
    data: List[Dict[str, Any]] = [{"Дата операции": "15.01.2023 12:30:45", "Категория": "Тест", "Кэшбэк": ""}]

    result: str = profitable_cashback_categories(data, 2023, 1)
    result_data: Dict[str, float] = json.loads(result)

    assert result_data == {"Тест": 0.0}


def test_find_personal_transfers_success(sample_transactions: List[Dict[str, Any]]) -> None:
    """Тест успешного поиска переводов физическим лицам."""
    result: str = find_personal_transfers(test_transactions)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert len(result_data) == 2
    assert all(t["Категория"] == "Переводы" for t in result_data)
    assert all("." in t["Описание"] for t in result_data)


def test_find_personal_transfers_no_matches(sample_transactions: List[Dict[str, Any]]) -> None:
    """Тест поиска переводов, когда нет подходящих данных."""
    no_transfers: List[Dict[str, Any]] = [t for t in test_transactions if t["Категория"] != "Переводы"]

    result: str = find_personal_transfers(no_transfers)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert result_data == []


def test_find_personal_transfers_empty() -> None:
    """Тест поиска переводов в пустом списке транзакций."""
    result: str = find_personal_transfers([])
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert result_data == []


def test_personal_transfers_correct_format() -> None:
    """Тест поиска переводов с корректным форматом имени."""
    data: List[Dict[str, Any]] = [
        {"Дата операции": "10.01.2023 18:20:11", "Категория": "Переводы", "Кэшбэк": "0", "Описание": "Иван П."}
    ]

    result: str = find_personal_transfers(data)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert len(result_data) == 1


def test_personal_transfers_wrong_format() -> None:
    """Тест поиска переводов с некорректным форматом имени."""
    data: List[Dict[str, Any]] = [
        {
            "Дата операции": "10.01.2023 18:20:11",
            "Категория": "Переводы",
            "Кэшбэк": "0",
            "Описание": "Иван Петров",  # Нет точки
        }
    ]

    result: str = find_personal_transfers(data)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert result_data == []


def test_personal_transfers_none_description() -> None:
    """Тест поиска переводов с None в поле Описание."""
    data: List[Dict[str, Any]] = [
        {"Дата операции": "10.01.2023 18:20:11", "Категория": "Переводы", "Кэшбэк": "0", "Описание": None}
    ]

    result: str = find_personal_transfers(data)
    result_data: List[Dict[str, Any]] = json.loads(result)

    assert result_data == []
