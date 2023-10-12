"""Модуль логгирования операций"""
from setting import settings
import datetime
import os


def w_loggings(logdata):
    """Добавление записи в лог"""
    now = datetime.datetime.now()
    w_string = now.strftime("%d-%m-%Y %H:%M:%S")
    w_string = w_string + f": {logdata}"
    if os.path.isfile(settings.LOG_FILE):
        # проверка размера файла
        if os.path.getsize(settings.LOG_FILE) > 10485760 :

            with open(settings.LOG_FILE, 'w', encoding="UTF-8") as file:
                file.write(f" {w_string}\n")
        else:
            with open(settings.LOG_FILE, 'a', encoding="UTF-8") as file:
                file.write(f" {w_string}\n")
    else:
        with open(settings.LOG_FILE, 'w', encoding="UTF-8") as file:
            file.write(f" {w_string}\n")