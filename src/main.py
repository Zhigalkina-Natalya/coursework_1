import json
import logging
from typing import Any

from src.reports import spending_by_category, spending_by_weekday
from src.services import find_personal_transfers, profitable_cashback_categories, safe_input_year_month
from src.utils import read_operations
from src.views import get_main_page

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Основная функция запуска приложения для анализа банковских операций.
    Программа предлагает пользователю:
    1. Веб-страница "Главная" — вывод информации по указанной дате.
    2. Сервисы:
       - Выгодные категории повышенного кешбэка за указанный год и месяц.
       - Поиск переводов физическим лицам.
    3. Отчеты:
       - Траты по выбранной категории за последние 3 месяца.
       - Траты по дням недели за последние 3 месяца.

    Пользователь вводит необходимые данные (даты, год, месяц, категории),
    а функция обрабатывает их, вызывает соответствующие сервисы и выводит результаты.
    Обрабатываются некорректные или пустые вводы для года и месяца.
    """
    print("Добро пожаловать в приложение для анализа банковских операций!\n")
    print("1. Главная страница")
    print("2. Сервисы")
    print("3. Отчеты")

    choice = input("Выберите раздел: ")

    if choice == "1":
        date_str = input("Введите дату в формате YYYY-MM-DD HH:MM:SS: ")
        main_page_json = get_main_page(date_str)
        main_page_result: dict[str, Any] = json.loads(main_page_json)
        print(main_page_result)

    elif choice == "2":
        choice1 = input(
            "Выберите действие:\n"
            "1. Выгодные категории повышенного кешбэка\n"
            "2. Поиск переводов физическим лицам\n"
        )
        df = read_operations("data/operations.xlsx")
        # Преобразуем ключи словарей в str для корректного типа
        transactions_list: list[dict[str, Any]] = [
            {str(k): v for k, v in row.items()} for row in df.to_dict(orient="records")
        ]

        if choice1 == "1":
            year, month = safe_input_year_month()
            cashback_json = profitable_cashback_categories(transactions_list, year, month)
            cashback_result: dict[str, Any] = json.loads(cashback_json)
            print(cashback_result)

        elif choice1 == "2":
            transfers_json = find_personal_transfers(transactions_list)
            transfers_result: list[dict[str, Any]] = json.loads(transfers_json)
            print(transfers_result)

        else:
            print("Неверный выбор!")

    elif choice == "3":
        choice2 = input(
            "Выберите отчет:\n" "1. Траты по категории за 3 месяца\n" "2. Траты по дням недели за 3 месяца\n"
        )
        df = read_operations("data/operations.xlsx")

        if choice2 == "1":
            category = input("Введите категорию: ")
            date_str = input("Введите дату в формате DD.MM.YYYY: ")
            category_report = spending_by_category(df, category, date_str)
            print(category_report)

        elif choice2 == "2":
            date_str = input("Введите дату в формате DD.MM.YYYY: ")
            weekday_report = spending_by_weekday(df, date_str)
            print(weekday_report)

        else:
            print("Неверный выбор!")

    else:
        print("Неверный выбор!")


if __name__ == "__main__":
    main()
