from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# -------------------------------------------------
#   FASTAPI APP + CORS
# -------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при бажанні можеш обмежити своїм доменом
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КОДА
# -------------------------------------------------


def _reduce22(n: int) -> int:
    """Приводим число к диапазону 1..22 (вычитая 22)."""
    n = int(round(n))
    n = abs(n)
    if n == 0:
        return 22
    while n > 22:
        n -= 22
    return n


def _sum_digits(n: int) -> int:
    return sum(int(ch) for ch in str(abs(int(n))))


def _sum_digits_no_zero(n: int) -> int:
    return sum(int(ch) for ch in str(abs(int(n))) if ch != "0")


def _digital_root_9(n: int) -> int:
    """Цифровой корень до 1–9, как в нумерологии."""
    n = abs(int(n))
    if n == 0:
        return 0
    return 1 + ((n - 1) % 9)


def _card_diff(a: int, b: int) -> int:
    """Разность карт для кармы/камней: из большего вычитаем меньшее, 0 -> 22."""
    d = abs(int(a) - int(b))
    if d == 0:
        return 22
    return _reduce22(d)


def _parse_birth_date(value) -> date:
    """Принимает date / datetime / строку 'DD.MM.YYYY' / 'YYYY-MM-DD'."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        s = value.strip()
        # ISO 'YYYY-MM-DD'
        if "-" in s and len(s.split("-")[0]) == 4:
            return datetime.strptime(s, "%Y-%m-%d").date()
        # дд.мм.гггг / дд/мм/гггг / дд-мм-гггг
        for sep in (".", "/", "-"):
            if sep in s:
                d, m, y = s.split(sep)
                return date(int(y), int(m), int(d))
        raise ValueError(f"Не можу розібрати дату: {value!r}")
    raise TypeError(f"Очікував date/str, отримав {type(value)}")


def _add_years_safe(d: date, years: int) -> date:
    """Додає роки до дати, акуратно обробляючи 29 лютого."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=d.day - 1)


# -------------------------------------------------
#   СТРУКТУРЫ ДАННЫХ
# -------------------------------------------------


@dataclass
class TarotCode:
    birth_date: date

    day_card: int
    month_card: int
    year_card: int

    destiny1: int
    destiny2: int
    destiny3: int

    period_cards: list[int]
    period_ages: list[int]
    period_start_dates: list[date]

    karma_cards: list[int]
    gift_cards: list[int]
    stone_cards: list[int]


CARD_NAMES = {
    1: "MAGICIAN",
    2: "HIGH PRIESTESS",
    3: "EMPRESS",
    4: "EMPEROR",
    5: "HIEROPHANT",
    6: "LOVERS",
    7: "CHARIOT",
    8: "JUSTICE",
    9: "HERMIT",
    10: "FORTUNE",
    11: "STRENGTH",
    12: "HANGED MAN",
    13: "DEATH",
    14: "TEMPERANCE",
    15: "DEVIL",
    16: "TOWER",
    17: "STAR",
    18: "MOON",
    19: "SUN",
    20: "JUDGEMENT",
    21: "WORLD",
    22: "FOOL",
}


# -------------------------------------------------
#   РАСЧЁТ КОДА ЧЕЛОВЕКА
# -------------------------------------------------


def calc_tarot_code(birth) -> TarotCode:
    """
    Основной расчёт по дате рождения.
    birth: date / datetime / строка "18.06.1984" / "1984-06-18".
    """
    bd = _parse_birth_date(birth)
    d = bd.day
    m = bd.month
    y = bd.year

    # Базовые карты
    day_card = _reduce22(d)
    month_card = m  # 1–12, без редукції
    year_card = _reduce22(_sum_digits(y))

    # Главная карта судьбы: сумма всех цифр даты без нулей
    sum_no_zero = (
        _sum_digits_no_zero(d)
        + _sum_digits_no_zero(m)
        + _sum_digits_no_zero(y)
    )
    destiny1 = _reduce22(sum_no_zero)

    # Вторая карта судьбы: день + месяц + год
    destiny2 = _reduce22(day_card + month_card + year_card)

    # Третья карта судьбы: цифровой корень дня + месяца + года
    dr_day = _digital_root_9(d)
    dr_month = _digital_root_9(m)
    dr_year = _digital_root_9(y)
    destiny3 = _reduce22(dr_day + dr_month + dr_year)

    # Периоды жизни (4 карты)
    p1 = _reduce22(day_card + month_card)
    p2 = _reduce22(day_card + year_card)
    p3 = _reduce22(p1 + p2)
    p4 = _reduce22(month_card + year_card)
    period_cards = [p1, p2, p3, p4]

    # Карма (4 карты) – разности
    k1 = _card_diff(month_card, day_card)   # день и месяц
    k2 = _card_diff(day_card, year_card)    # день и год
    k3 = _card_diff(p1, p2)                 # разность первых двух периодов
    k4 = _card_diff(month_card, year_card)  # месяц и год
    karma_cards = [k1, k2, k3, k4]

    # Дары (2 карты)
    g1 = _reduce22(day_card + destiny1)
    g2 = _reduce22(day_card + destiny2)
    gift_cards = [g1, g2]

    # Камни преткновения (2 карты)
    s1 = _card_diff(destiny1, day_card)
    s2 = _card_diff(destiny2, day_card)
    stone_cards = [s1, s2]

    # Возраст начала периодов
    dr = _digital_root_9(sum_no_zero)
    start2 = 36 - dr
    period_ages = [0, start2, start2 + 9, start2 + 18]

    # Реальные даты начала периодов
    period_start_dates = [
        _add_years_safe(bd, age) for age in period_ages
    ]

    return TarotCode(
        birth_date=bd,
        day_card=day_card,
        month_card=month_card,
        year_card=year_card,
        destiny1=destiny1,
        destiny2=destiny2,
        destiny3=destiny3,
        period_cards=period_cards,
        period_ages=period_ages,
        period_start_dates=period_start_dates,
        karma_cards=karma_cards,
        gift_cards=gift_cards,
        stone_cards=stone_cards,
    )


# -------------------------------------------------
#   СОВМЕСТИМОСТЬ
# -------------------------------------------------

POSITIVE_CARDS = {21, 17, 19, 11, 10, 7, 5, 3}
NEGATIVE_CARDS = {16, 12, 22, 13, 15, 18, 9}
GOOD_MARRIAGE_CARDS = {3, 5, 6, 8, 14, 17, 19, 21}
BAD_MARRIAGE_CARDS = {22, 9, 12, 13, 15, 16, 18, 20}
ACTIVE_CARDS = {1, 4, 5, 7, 11, 15, 16, 19}
PASSIVE_CARDS = {2, 3, 6, 9, 12, 14, 18, 21}


def _main_destiny_from_birth(birth) -> int:
    """Главная карта судьбы по дате – как в методике."""
    bd = _parse_birth_date(birth)
    d = bd.day
    m = bd.month
    y = bd.year
    sum_no_zero = (
        _sum_digits_no_zero(d)
        + _sum_digits_no_zero(m)
        + _sum_digits_no_zero(y)
    )
    return _reduce22(sum_no_zero)


@dataclass
class CompatibilityResult:
    k1: int
    k2: int
    union: int
    p1: int
    p2: int
    total: int
    score: int
    level: str
    leader_text: str
    summary: str


def _card_score(card: int) -> int:
    base = 0
    if card in POSITIVE_CARDS:
        base += 2
    if card in NEGATIVE_CARDS:
        base -= 2
    if card in GOOD_MARRIAGE_CARDS:
        base += 1
    if card in BAD_MARRIAGE_CARDS:
        base -= 1
    return base


def _leader_text(p1: int, p2: int) -> str:
    p1_active = p1 in ACTIVE_CARDS
    p1_passive = p1 in PASSIVE_CARDS
    p2_active = p2 in ACTIVE_CARDS
    p2_passive = p2 in PASSIVE_CARDS

    if p1_active and p2_passive:
        return "Ініціативу частіше бере партнер 1."
    if p2_active and p1_passive:
        return "Ініціативу частіше бере партнер 2."
    return "Роль лідера може переходити від одного партнера до іншого — важливо домовлятися."


def calc_compatibility(birth1, birth2) -> CompatibilityResult:
    """Совместимость двух партнёров."""
    k1 = _main_destiny_from_birth(birth1)
    k2 = _main_destiny_from_birth(birth2)

    union = _reduce22(k1 + k2)
    p1 = _reduce22(k1 + union)
    p2 = _reduce22(k2 + union)
    total = _reduce22(union + p1 + p2)

    cards = [union, p1, p2, total]

    score = (
        _card_score(union) * 3 +
        _card_score(total) * 3 +
        _card_score(p1) +
        _card_score(p2)
    )

    if score >= 8:
        level = "Висока, гармонійна сумісність"
    elif score >= 2:
        level = "Середня сумісність: союз робочий, але потребує уваги"
    elif score >= -4:
        level = "Складна, кармічна сумісність: потрібен високий рівень усвідомленості"
    else:
        level = "Дуже напружена сумісність: без роботи над собою стосунки можуть бути важкими"

    positives = []
    negatives = []

    gm = [c for c in cards if c in GOOD_MARRIAGE_CARDS]
    love = [c for c in cards if c in {2, 3, 4, 5, 6, 18, 19, 20}]
    conflict = [c for c in cards if c in {13, 15, 16}]

    if gm:
        positives.append(
            "є карти довгого та стабільного союзу: " +
            ", ".join(CARD_NAMES[c] for c in gm)
        )
    if love:
        positives.append(
            "союз сильно про почуття та особисте життя: " +
            ", ".join(CARD_NAMES[c] for c in love)
        )
    if conflict:
        negatives.append(
            "присутня вибухова / конфліктна енергія: " +
            ", ".join(CARD_NAMES[c] for c in conflict)
        )

    leader_text = _leader_text(p1, p2)

    summary_parts = [level + "."]
    if positives:
        summary_parts.append("Плюси: " + "; ".join(positives) + ".")
    if negatives:
        summary_parts.append("Ризики: " + "; ".join(negatives) + ".")
    summary_parts.append(leader_text)
    summary = " ".join(summary_parts)

    return CompatibilityResult(
        k1=k1,
        k2=k2,
        union=union,
        p1=p1,
        p2=p2,
        total=total,
        score=score,
        level=level,
        leader_text=leader_text,
        summary=summary,
    )


# -------------------------------------------------
#   API-ЕНДПОИНТЫ
# -------------------------------------------------


@app.get("/api/tarot")
def api_tarot(date: str = Query(..., description="Дата у форматі 18.06.1984 або 1984-06-18")):
    """
    Розрахунок коду для однієї дати.
    Повертає:
      - карти долі, періодів, карми, дарів, камені
      - вік початку періодів
      - реальні дати початку періодів (ISO-формат)
    """
    try:
        code = calc_tarot_code(date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "input": date,
        "result": {
            "dayCard": code.day_card,
            "monthCard": code.month_card,
            "yearCard": code.year_card,
            "destiny1": code.destiny1,
            "destiny2": code.destiny2,
            "destiny3": code.destiny3,
            "periods": code.period_cards,
            "periodAges": code.period_ages,
            "periodStartDates": [d.isoformat() for d in code.period_start_dates],
            "karmas": code.karma_cards,
            "gifts": code.gift_cards,
            "stones": code.stone_cards,
        },
    }


@app.get("/api/compat")
def api_compat(
    date1: str = Query(..., description="Дата народження партнера 1"),
    date2: str = Query(..., description="Дата народження партнера 2"),
):
    """
    Сумісність двох партнерів.
    Повертає карти КС1/КС2, союзу, що отримує кожен, підсумок союзу,
    числовий бал, рівень та текстовий опис.
    """
    try:
        res = calc_compatibility(date1, date2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "input": {"partner1": date1, "partner2": date2},
        "result": {
            "k1": res.k1,
            "k2": res.k2,
            "union": res.union,
            "unionName": CARD_NAMES[res.union],
            "p1": res.p1,
            "p1Name": CARD_NAMES[res.p1],
            "p2": res.p2,
            "p2Name": CARD_NAMES[res.p2],
            "total": res.total,
            "totalName": CARD_NAMES[res.total],
            "score": res.score,
            "level": res.level,
            "leaderText": res.leader_text,
            "summary": res.summary,
        },
    }
