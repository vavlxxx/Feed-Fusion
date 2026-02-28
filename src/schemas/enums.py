from enum import Enum


class NewsCategory(str, Enum):
    INTERNATIONAL = "Международные отношения"
    CULTURE = "Культура"
    SCIENCETECH = "Наука и технологии"
    SOCIETY = "Общество"
    ECONOMICS = "Экономика"
    INCIDENTS = "Происшествия"
    SPORT = "Спорт"
    MEDICINE = "Здоровье"
