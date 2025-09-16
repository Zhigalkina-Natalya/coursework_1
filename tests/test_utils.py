import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils import (greeting_by_time, group_card, parse_datetime, read_operations, read_user_settings,
                       top_transactions)


def test_read_operations_mock() -> None:
    """
    Тест проверяет функцию read_operations, используя mock вместо реального файла.
    Мы подменяем pd.read_excel, чтобы вернуть заранее подготовленный DataFrame.
    """
    fake_df = pd.DataFrame({"Дата операции": ["2024-09-06"], "Сумма операции": [1000]})
    with patch("src.utils.pd.read_excel", return_value=fake_df) as mock_read_excel:
        result_df = read_operations("любой_путь.xlsx")

        pd.testing.assert_frame_equal(result_df, fake_df)

        mock_read_excel.assert_called_once()
        # Проверяем, что путь заканчивается на наш файл
        args, kwargs = mock_read_excel.call_args
        assert str(args[0]).endswith("любой_путь.xlsx")


def test_read_operations_file_not_found() -> None:
    """
    Проверяет, что при отсутствии файла выбрасывается ошибка FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        read_operations("non_existent_file.xlsx")


def test_read_operations_invalid_format(tmp_path: Path) -> None:
    """
    Проверяет, что при чтении не-Excel файла возникает ошибка.
    """
    # создаем текстовый файл вместо Excel
    file_path = tmp_path / "not_excel.txt"
    file_path.write_text("какой-то текст")

    with pytest.raises(Exception):
        read_operations(str(file_path))


def test_parse_datetime_valid() -> None:
    """Корректная дата парсится правильно."""
    date_str = "2024-09-06 15:30:45"
    expected = datetime(2024, 9, 6, 15, 30, 45)
    result = parse_datetime(date_str)
    assert result == expected


def test_parse_datetime_invalid_returns_now_simple() -> None:
    """Некорректная строка возвращает datetime.now()."""
    before = datetime.now()
    result = parse_datetime("invalid_date")
    after = datetime.now()
    # Проверяем, что результат попадает в диапазон [before, after]
    assert before <= result <= after


def test_parse_datetime_invalid_value_returns_now() -> None:
    """Некорректная дата (например, 31 февраля) возвращает datetime.now()."""
    before = datetime.now()
    result = parse_datetime("2024-02-31 10:00:00")
    after = datetime.now()
    assert before <= result <= after


@pytest.mark.parametrize(
    "date_str",
    [
        None,  # если передан None
        "",  # пустая строка
        "2021",  # совсем некорректный формат
        "06-09-2024",  # неправильный формат
    ],
)
def test_parse_datetime_various_invalid_inputs(date_str: str) -> None:
    """Разные некорректные варианты возвращают datetime.now()."""
    before = datetime.now()
    result = parse_datetime(date_str)
    after = datetime.now()
    assert before <= result <= after


def test_parse_datetime_leap_year() -> None:
    """
    Проверяет работу с високосным годом (29 февраля 2024).
    """
    date_str = "2024-02-29 12:00:00"
    expected = datetime(2024, 2, 29, 12, 0, 0)

    result = parse_datetime(date_str)
    assert result == expected


def test_greeting_by_time() -> None:
    assert greeting_by_time(datetime(2025, 8, 1, 7, 0, 0)) == "Доброе утро"
    assert greeting_by_time(datetime(2025, 8, 1, 13, 0, 0)) == "Добрый день"
    assert greeting_by_time(datetime(2025, 8, 1, 18, 0, 0)) == "Добрый вечер"
    assert greeting_by_time(datetime(2025, 8, 1, 23, 0, 0)) == "Доброй ночи"


@pytest.mark.parametrize(
    "transactions, expected",
    [
        (
            [{"Номер карты": "*1111", "Сумма платежа": "-735,00"}],
            [{"last_digits": "1111", "total_spent": 735.00, "cashback": 7.35}],
        ),
        (
            [{"Номер карты": "*2222", "Сумма платежа": "500,00"}],
            [],
        ),
        (
            [{"Номер карты": "*3333", "Сумма платежа": "abc"}],
            [],
        ),
        (
            [{"Сумма платежа": "-100,00"}],
            [{"last_digits": "0000", "total_spent": 100.00, "cashback": 1.00}],
        ),
        (
            [
                {"Номер карты": "*4444", "Сумма платежа": "-100,00"},
                {"Номер карты": "*4444", "Сумма платежа": "-50,00"},
            ],
            [{"last_digits": "4444", "total_spent": 150.00, "cashback": 1.50}],
        ),
        (
            [
                {"Номер карты": "*5555", "Сумма платежа": "-200,00"},
                {"Номер карты": "*6666", "Сумма платежа": "-300,00"},
            ],
            [
                {"last_digits": "5555", "total_spent": 200.00, "cashback": 2.00},
                {"last_digits": "6666", "total_spent": 300.00, "cashback": 3.00},
            ],
        ),
        (
            [{"Номер карты": "*7777", "Сумма платежа": "-100,235"}],
            [{"last_digits": "7777", "total_spent": 100.23, "cashback": 1.00}],
        ),
    ],
)
def test_group_card(transactions: List[Dict], expected: List[Dict]) -> None:
    """
    Параметризированный тест для функции group_card.
    Проверяет все ветви: расходы, доходы, ошибки парсинга,
    отсутствие номера карты, суммирование по картам и округление.
    """
    result = group_card(transactions)

    # Сортируем, чтобы порядок не влиял на проверку
    result_sorted = sorted(result, key=lambda x: x["last_digits"])
    expected_sorted = sorted(expected, key=lambda x: x["last_digits"])

    assert result_sorted == expected_sorted


def test_returns_top_transactions(sample_transactions: list[dict[str, Any]]) -> None:
    result = top_transactions(sample_transactions, top_n=3)
    assert len(result) == 3  # должно вернуться ровно 3 транзакции


def test_sorted_by_abs_amount(sample_transactions: list[dict[str, Any]]) -> None:
    result = top_transactions(sample_transactions, top_n=2)
    amounts = [abs(t["amount"]) for t in result]
    assert amounts == sorted(amounts, reverse=True)  # отсортировано по убыванию


def test_date_format(sample_transactions: list[dict[str, Any]]) -> None:
    result = top_transactions(sample_transactions, top_n=1)
    assert result[0]["date"].count(".") == 2  # проверяем формат ДД.ММ.ГГГГ


def test_contains_only_required_fields(sample_transactions: list[dict[str, Any]]) -> None:
    result = top_transactions(sample_transactions, top_n=1)[0]
    assert set(result.keys()) == {"date", "amount", "category", "description"}


def test_empty_transactions() -> None:
    """Функция должна вернуть пустой список, если транзакций нет."""
    result = top_transactions([], top_n=5)
    assert result == []


def test_transactions_less_than_top_n(sample_transactions: list[dict[str, Any]]) -> None:
    """Если транзакций меньше, чем top_n — возвращаются все."""
    result = top_transactions(sample_transactions[:2], top_n=5)
    assert len(result) == 2


def test_invalid_amount_format() -> None:
    """Некорректные суммы должны обрабатываться как 0.0"""
    transactions = [
        {"Дата операции": "01.01.2021", "Сумма платежа": "abc", "Категория": "Тест", "Описание": "Некорректная сумма"},
        {
            "Дата операции": "02.01.2021",
            "Сумма платежа": "1000,00",
            "Категория": "Тест",
            "Описание": "Корректная сумма",
        },
    ]
    result = top_transactions(transactions, top_n=2)
    assert any(t["amount"] == 0.0 for t in result)  # есть хотя бы одна нулевая сумма
    assert any(t["amount"] == 1000.0 for t in result)


def test_invalid_date_format() -> None:
    tx = [{"Дата операции": "2021-12-01", "Сумма платежа": "100"}]
    result = top_transactions(tx, top_n=1)
    assert result[0]["date"] == "01.12.2021"


def test_missing_fields() -> None:
    """Если каких-то полей нет, подставляются пустые строки."""
    transactions = [{"Дата операции": "01.01.2021", "Сумма платежа": "100,00"}]  # нет категории и описания
    result = top_transactions(transactions, top_n=1)[0]
    assert result["category"] == ""
    assert result["description"] == ""


def test_read_user_settings_file_exists(tmp_path: Path) -> None:
    """Тест успешного чтения настроек из файла"""
    settings: Dict[str, Any] = {"user_currencies": ["GBP"], "user_stocks": ["TSLA"]}
    file_path = tmp_path / "user_settings.json"
    file_path.write_text(json.dumps(settings), encoding="utf-8")

    result = read_user_settings(str(file_path))
    assert result == settings


def test_read_user_settings_file_not_found(tmp_path: Path) -> None:
    """Проверяем возврат значений по умолчанию при отсутствии файла"""
    fake_file = tmp_path / "not_exist.json"
    result = read_user_settings(str(fake_file))

    assert result == {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "MSFT"]}
