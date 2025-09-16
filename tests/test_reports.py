import logging
from datetime import datetime
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from pytest import LogCaptureFixture

from src.reports import parse_date, save_report, spending_by_category, spending_by_weekday


@pytest.mark.parametrize(
    "category,date_str,expected",
    [
        ("еда", "20.03.2023", 1200),
        ("транспорт", "20.03.2023", 300),
        ("еда", "15.01.2023", 650),
    ],
)
def test_spending_by_category(sample_data: pd.DataFrame, category: str, date_str: str, expected: float) -> None:
    result = spending_by_category(sample_data, category, date_str)
    assert result is not None
    assert isinstance(result, dict)
    assert result["category"] == category
    assert result["total_spent"] == expected


def test_spending_by_category_invalid_date(sample_data: pd.DataFrame) -> None:
    """Некорректная дата → функция возвращает None"""
    result = spending_by_category(sample_data, "Еда", "invalid")
    assert result is None


def test_spending_by_weekday_structure(sample_data: pd.DataFrame) -> None:
    """Проверка структуры результата функции spending_by_weekday."""
    result = spending_by_weekday(sample_data, "20.03.2023")
    assert result is not None
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)
    assert all("weekday" in r and "Сумма платежа" in r for r in result)


def test_spending_by_weekday_values(sample_data: pd.DataFrame) -> None:
    result = spending_by_weekday(sample_data, "20.03.2023")
    assert result is not None
    weekdays = {r["weekday"]: r["Сумма платежа"] for r in result}
    assert "Tuesday" in weekdays
    assert weekdays["Tuesday"] > 0


def test_spending_by_weekday_invalid_date(sample_data: pd.DataFrame) -> None:
    """Некорректная дата → возвращает None"""
    result = spending_by_weekday(sample_data, "invalid")
    assert result is None


def test_spending_by_weekday_empty_dataframe() -> None:
    df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа"])
    result = spending_by_weekday(df, "20.03.2023")
    assert result == []


# Тесты к parse_date
@pytest.mark.parametrize(
    "date_str,expected",
    [
        ("15.03.2025", datetime(2025, 3, 15)),
        ("01.01.2020", datetime(2020, 1, 1)),
    ],
)
def test_parse_date_valid(date_str: str, expected: datetime) -> None:
    dt = parse_date(date_str)
    assert dt is not None
    assert dt.year == expected.year
    assert dt.month == expected.month
    assert dt.day == expected.day


def test_parse_date_empty(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    dt = parse_date("")
    assert dt is None
    assert "Введите дату" in caplog.text


@pytest.mark.parametrize(
    "date_str",
    ["2025-03-15", "abc", "", None],
)
def test_parse_date_invalid(date_str: str | None) -> None:
    dt = parse_date(date_str)
    assert dt is None


# Проверка декоратора save_report
def test_save_report_creates_file_and_logs(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)

    @save_report
    def dummy_func() -> dict[str, int]:
        return {"test": 123}

    with patch("builtins.open", mock_open()) as mocked_file:
        result = dummy_func()
        mocked_file.assert_called_once_with("dummy_func.json", "w", encoding="utf-8")
        assert result == {"test": 123}
        assert "Отчет сохранен" in caplog.text


def test_save_report_handles_exception(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)

    @save_report
    def dummy_func() -> dict[str, int]:
        return {"test": 123}

    with patch("builtins.open", side_effect=Exception("fail")):
        result = dummy_func()
        assert result == {"test": 123}
        assert "Ошибка при сохранении отчета" in caplog.text
