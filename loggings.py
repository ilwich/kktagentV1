"""Модуль логгирования операций"""
from setting import settings
import datetime


def w_loggings(logdata):
    """Добавление записи в лог"""
    now = datetime.datetime.now()
    w_string = now.strftime("%d-%m-%Y %H:%M:%S")
    w_string = w_string + f": {logdata}"
    with open(settings.LOG_FILE, 'a', encoding="UTF-8") as file:
        file.write(f" {w_string}\n")