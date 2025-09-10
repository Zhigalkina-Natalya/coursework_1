import pytest

from src.reports import spending_by_category, spending_by_weekday


@pytest.mark.parametrize(
    "category,date_str,expected",
    [
        ("Еда", "20.03.2023", 1200),
        ("Транспорт", "20.03.2023", 300),
        ("Еда", "15.01.2023", 650),  # только январские траты
    ],
)
def test_spending_by_category(sample_data, category: str, date_str: str, expected: float) -> None:
    """Проверка функции spending_by_category на разных входных данных."""
    result = spending_by_category(sample_data, category, date_str)
    assert isinstance(result, dict)
    assert result["category"] == category
    assert result["total_spent"] == expected


def test_spending_by_weekday_structure(sample_data) -> None:
    """Проверка структуры результата функции spending_by_weekday."""
    result = spending_by_weekday(sample_data, "20.03.2023")
    assert isinstance(result, list)
    assert all(isinstance(r, dict) for r in result)
    assert all("weekday" in r and "Сумма операции" in r for r in result)


def test_spending_by_weekday_values(sample_data) -> None:
    """Проверка, что суммы по дням недели корректно считаются (по модулю)."""
    result = spending_by_weekday(sample_data, "20.03.2023")
    weekdays = {r["weekday"]: r["Сумма операции"] for r in result}
    assert "Tuesday" in weekdays  # были траты во вторник
    assert weekdays["Tuesday"] > 0
