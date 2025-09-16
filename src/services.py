import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def safe_input_year_month() -> tuple[int, int]:
    """
    Запрашивает у пользователя год и месяц, при пустом или некорректном вводе
    возвращает текущий год и месяц
    """
    now = datetime.now()

    year_input = input("Введите год: ").strip()
    try:
        year = int(year_input) if year_input else now.year
        if year_input == "":
            logger.info("Год не введён, используется текущий год: %d", year)
    except ValueError:
        print(f"Неверный формат года '{year_input}', используется текущий: {now.year}")
        logger.warning("Некорректный ввод года '%s', используется текущий: %d", year_input, now.year)
        year = now.year

    month_input = input("Введите месяц: ").strip()
    try:
        month = int(month_input) if month_input else now.month
        if month_input == "":
            logger.info("Месяц не введён, используется текущий месяц: %d", month)
        if not 1 <= month <= 12:
            print(f"Месяц вне диапазона 1-12, используется текущий: {now.month}")
            logger.warning("Месяц вне диапазона 1-12 ('%s'), используется текущий: %d", month_input, now.month)
            month = now.month
    except ValueError:
        print(f"Неверный формат месяца '{month_input}', используется текущий: {now.month}")
        logger.warning("Некорректный ввод месяца '%s', используется текущий: %d", month_input, now.month)
        month = now.month

    return year, month


def profitable_cashback_categories(data: List[Dict[str, Any]], year: int, month: int) -> str:
    """
    Анализирует транзакции и возвращает JSON с расчетом кешбэка по категориям за указанный месяц/год.
    Если год или месяц не указаны или указаны неверно — используется текущие значения.
    data: список транзакций [{"Дата операции": "...", "Категория": "...", "Бонусы (включая кэшбэк)": "..."}]
    JSON-строка вида { "Категория": сумма_кешбэка }
    """
    try:
        logging.info("Фильтрация транзакций за %02d.%d", month, year)

        # фильтрация по дате
        filtered = list(
            filter(
                lambda t: datetime.strptime(str(t["Дата операции"]), "%d.%m.%Y %H:%M:%S").year == year
                and datetime.strptime(str(t["Дата операции"]), "%d.%m.%Y %H:%M:%S").month == month,
                data,
            )
        )

        if not filtered:
            logging.warning("Нет транзакций за указанный период %02d.%d", month, year)
            return json.dumps({})

        # преобразуем строки с кешбэком в float (если пусто → 0)
        transactions = list(
            map(
                lambda t: {
                    "Категория": t["Категория"],
                    "Кэшбэк": float(str(t.get("Бонусы (включая кэшбэк)", 0)).replace(",", ".") or 0),
                },
                filtered,
            )
        )

        # агрегируем по категориям
        cashback_by_category: Dict[str, float] = {}
        for t in transactions:
            category = t["Категория"]
            cashback = t["Кэшбэк"]
            cashback_by_category[category] = cashback_by_category.get(category, 0) + cashback

        logging.info("Рассчитан кешбэк по %d категориям", len(cashback_by_category))

        # сортировка категорий по сумме кешбэка (по убыванию)
        cashback_by_category = dict(sorted(cashback_by_category.items(), key=lambda x: x[1], reverse=True))

        return json.dumps(cashback_by_category, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error("Ошибка при обработке транзакций: %s", e)
        return json.dumps({})


def find_personal_transfers(transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет переводы физическим лицам. Условие: Категория = 'Переводы' и в 'Описание' есть 'Имя Ф.'
    Возвращается JSON-ответ со всеми переводами физлицам
    """
    try:
        # регулярка: Имя (с заглавной буквы) + пробел + Инициал (заглавная буква + точка)
        pattern = re.compile(r"^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.$")

        results = [
            t
            for t in transactions
            if t.get("Категория") == "Переводы" and pattern.match(str(t.get("Описание", "")).strip())
        ]

        logging.info(f"Поиск переводов физлицам: найдено {len(results)} записей")

        return json.dumps(results, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Ошибка в find_personal_transfers: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
