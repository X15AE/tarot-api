from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# Дозволяємо CORS, щоб до API могла стукатись сторінка з іншого домену
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потім можна обмежити своїм доменом
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# --------------------------

def tarot_reduce22(n: int) -> int:
    n = int(abs(int(n)))
    while n > 22:
        n -= 22
    if n == 0:
        n = 22
    return n


def tarot_digit_root9(n: int) -> int:
    n = int(abs(int(n)))
    if n == 0:
        return 0
    return 1 + ((n - 1) % 9)


def tarot_sum_digits(n: int) -> int:
    s = 0
    for ch in str(int(abs(int(n)))):
        s += int(ch)
    return s


def tarot_sum_date_digits_no_zero(day: int, month: int, year: int) -> int:
    s = 0
    for part in (day, month, year):
        for ch in str(part):
            if ch != "0":
                s += int(ch)
    return s


def tarot_parse_date(value: str) -> datetime:
    """
    Підтримує формати:
    - dd.mm.yyyy
    - dd/mm/yyyy
    - dd-mm-yyyy
    - плюс стандартний ISO 'yyyy-mm-dd'
    """
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValueError('Дата має бути рядком, напр. "28.10.1986"')

    s = value.strip()

    # Пробуємо dd.mm.yyyy / dd/mm/yyyy / dd-mm-yyyy
    for sep in [".", "/", "-"]:
        parts = s.split(sep)
        if len(parts) == 3 and len(parts[2]) == 4:
            try:
                d = int(parts[0])
                mo = int(parts[1])
                y = int(parts[2])
                return datetime(y, mo, d)
            except ValueError:
                pass

    # Потім пробуємо ISO yyyy-mm-dd
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass

    raise ValueError('Аргумент має бути датою формату "28.10.1986" або "1986-10-28".')


def tarot_compute_all(value: str) -> dict:
    dt = tarot_parse_date(value)

    day = dt.day           # 1–31
    month = dt.month       # 1–12
    year = dt.year

    # Карта дня
    day_card = tarot_reduce22(day)

    # Карта месяца
    month_card = month  # 1–12

    # Карта года: сума цифр року → редукція до 1–22
    year_card = tarot_reduce22(tarot_sum_digits(year))

    # 1-я карта судьбы: сумма всех цифр даты без нулей
    destiny1 = tarot_reduce22(tarot_sum_date_digits_no_zero(day, month, year))

    # 2-я карта судьбы: день + месяц + год (карты)
    destiny2 = tarot_reduce22(day_card + month_card + year_card)

    # 3-я карта: цифровые корни дня/месяца/года → сумма → редукция до 1–22
    dr_day = tarot_digit_root9(day)
    dr_month = tarot_digit_root9(month)
    dr_year = tarot_digit_root9(year)
    destiny3 = tarot_reduce22(dr_day + dr_month + dr_year)

    # Карты даров
    gift1 = tarot_reduce22(day_card + destiny1)
    gift2 = tarot_reduce22(day_card + destiny2)

    # Камни преткновения
    def stone(a: int, b: int) -> int:
        d = abs(a - b)
        if d == 0:
            return 22
        return tarot_reduce22(d)

    stone1 = stone(destiny1, day_card)
    stone2 = stone(destiny2, day_card)

    # Периоды жизни
    period1 = tarot_reduce22(day_card + month_card)
    period2 = tarot_reduce22(day_card + year_card)
    period3 = tarot_reduce22(period1 + period2)
    period4 = tarot_reduce22(month_card + year_card)

    # Кармы
    def karma(a: int, b: int) -> int:
        d = abs(a - b)
        if d == 0:
            return 22
        return tarot_reduce22(d)

    karma1 = karma(day_card, month_card)
    karma2 = karma(day_card, year_card)
    karma3 = karma(period1, period2)
    karma4 = karma(month_card, year_card)

    return {
        "dayCard": day_card,
        "monthCard": month_card,
        "yearCard": year_card,
        "destiny1": destiny1,
        "destiny2": destiny2,
        "destiny3": destiny3,
        "birth":   [day_card, destiny1, destiny2, destiny3],
        "gifts":   [gift1, gift2],
        "stones":  [stone1, stone2],
        "periods": [period1, period2, period3, period4],
        "karmas":  [karma1, karma2, karma3, karma4],
    }


from fastapi import Query

@app.get("/api/tarot")
def get_tarot(date: str = Query(..., description="Дата у форматі 18.06.1984 або 1984-06-18")):
    """
    Виклик: /api/tarot?date=18.06.1984 або /api/tarot?date=1984-06-18
    """
    try:
        result = tarot_compute_all(date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "input": date,
        "result": result,
    }
