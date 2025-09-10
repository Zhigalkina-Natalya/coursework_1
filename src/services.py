import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def profitable_cashback_categories(data: List[Dict[str, Any]], year: int, month: int) -> str:
    """
    Анализирует транзакции и возвращает JSON с расчетом кешбэка по категориям за указанный месяц/год.
    Возвращается JSON-строка вида {"Категория 1": сумма, Категория 2": сумма, ...}
    """
    try:
        # фильтруем по дате
        filtered = list(
            filter(
                lambda x: datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S").year == year
                and datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S").month == month,
                data,
            )
        )

        # группировка по категориям
        categories: Dict[str, float] = {}
        for t in filtered:
            cashback = float(t.get("Кэшбэк", 0) or 0)
            cat = t.get("Категория", "Другое")
            categories[cat] = categories.get(cat, 0) + cashback

        logging.info(f"Анализ выгодных категорий завершён, найдено {len(categories)} категорий")

        return json.dumps(categories, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Ошибка в profitable_cashback_categories: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
