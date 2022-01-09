"""Модуль обмена с сервером Инкотекса"""
import requests
from icecream import ic
from setting import settings
from models import *
from loggings import w_loggings

def inc_get_drvinfo():
    """ Получаем версию драйвера на сервере Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес сервера кассы
    data = {"command": "GetDriverInfo"}
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл kkt.txt
    if response_on_python['result'] == 0 :
        w_loggings(f"Version of driver  {response_on_python['driverVer']}")
        return "Connecting with Incerman OK"
    else:
        return f"Error conection Incerman {response_on_python['description']}"


def inc_open_session():
    """ Получение статуса кассы на сервере Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": None,
            "command": "OpenSession",
            "portName": settings.INC_PORTNAME,
            "debug": "false",
            "logPath": "c:\projects\kktagent",
            "model": "185F"
            }
    try_count = 0
    while try_count < settings.INC_TRY_COUNT:
        response = requests.post(url, json=data, headers=headers)
        # Поскольку данные пришли в формате json, переведем их в python
        response_on_python = response.json()
        try_count += 1
        if response_on_python['result'] == 0:
            break

    # Запишем полученные данные в файл лога
    if response_on_python['result'] == 0:
        w_loggings(f"SessionKey is {response_on_python['sessionKey']}")
        return response_on_python['sessionKey']
    else:
        w_loggings(f'Ошибка подключения к серверу Инкотекс {response_on_python["description"]}')
        return '0'


def inc_close_session(session_key):
    """ Закрытие сессии на сервере Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": session_key,
            "command": "CloseSession",
            }
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лога
    if response_on_python['result'] == 0 :
        w_loggings(f"SessionKey {session_key} is  close")
        return f"Session is close."
    else:
        return False


def inc_get_status(session_key):
    """ Запрос статуса на сервере Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": session_key,
            "command": "GetStatus",
            }
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0 :
        w_loggings(f"Получены данные о статусе кассы {response_on_python['fnInfo']['fnNum']}")
        res = {
            'fn_number': response_on_python['fnInfo']['fnNum'],
            'shft_num': response_on_python['shiftInfo']['num'],
            'shft_isopen': response_on_python['shiftInfo']['isOpen'],
            'is24Expired': response_on_python['shiftInfo']['is24Expired'],
            'date_time': response_on_python['dateTime']
        }
        return res
    else:
        return False


def inc_open_shift(session_key, kkt):
    """ Открытие смены на кассе сервера Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": session_key,
            "command": "OpenShift",
            'printDoc': settings.PRINT_DOC,
            'cashierInfo': {
                            'cashierName': kkt.cashier_name,
                            'cashierINN': kkt.cashier_inn
            }
    }
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0:
        w_loggings(f"Открыта смена № {response_on_python['shiftNum']} на кассе {kkt.fn_number}")
        res = {
            'shft_num': response_on_python['shiftNum']
        }
        return res
    else:
        return False


def inc_close_shift(session_key, kkt):
    """ Закрытие смены на кассе сервера Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": session_key,
            "command": "CloseShift",
            'printDoc': settings.PRINT_DOC,
            'cashierInfo': {
                            'cashierName': kkt.cashier_name,
                            'cashierINN': kkt.cashier_inn
            }
    }
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0:
        w_loggings(f"Закрыта смена № {response_on_python['shiftNum']} на кассе {kkt.fn_number}")
        res = {
            'shft_num': response_on_python['shiftNum']
        }
        return res
    else:
        return False


def inc_open_check(session_key, kkt, check_kkt, check_type=0):
    """ Открытие чека на кассе сервера Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта

    data = {"sessionKey": session_key,
            "command": "OpenCheck",
            "checkType": check_type,
            "taxSystem": int(check_kkt.tax_system),
            'printDoc': settings.PRINT_DOC,
            'cashierInfo': {
                            'cashierName': kkt.cashier_name,
                            'cashierINN': kkt.cashier_inn
            }
    }
    if check_kkt.buyer_name != '':
        data['buyerInfo'] = {'buyerName': check_kkt.buyer_name, 'buyerINN': check_kkt.buyer_inn}
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0:
        w_loggings(f"Открыт чек № {response_on_python['checkNum']} на кассе {kkt.fn_number}")
        res = {
            'shft_num': response_on_python['shiftNum'],
            'check_num': response_on_python['checkNum']
        }
        return res
    else:
        w_loggings(f"Ошибка открытия чека {response_on_python['description']}")
        return False


def inc_add_goods(session_key, kkt, good):
    """ Добавление товаров в чек на кассе сервера Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта
    data = {"sessionKey": session_key,
            "command": "AddGoods",
            "productName": good['product_name'],
            "qty": good['qty'],
            'taxCode': good['tax_code'],
            'productTypeCode': good['product_type_code'],
            'price': good['price']
            }
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0:
        w_loggings(f"Добавлен товар № {response_on_python['goodsNum']} на кассе {kkt.fn_number}")
        res = {
            'shft_num': response_on_python['shiftNum'],
            'check_num': response_on_python['checkNum']
            }
        return res
    else:
        return False


def inc_close_check(session_key, kkt, check_kkt):
    """ Закрытие чека на кассе сервера Инкотекс"""
    headers = {'ContentType': 'application/json; charset=utf-8'}
    url = settings.URL_INCERMAN  # Полный адрес эндпоинта

    data = {"sessionKey": session_key,
            "command": "CloseCheck",
            'payment': {
                            'cash': check_kkt.cash,
                            'ecash': check_kkt.ecash
            }
        }
    if check_kkt.send_check_to != '':
        data['sendCheckTo'] = check_kkt.send_check_to
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['result'] == 0:
        w_loggings(f"Закрыт чек № {response_on_python['checkNum']} на кассе {kkt.fn_number}")
        res = {
            'shft_num': response_on_python['shiftNum'],
            'check_num': response_on_python['checkNum'],
            'fiscal_doc_num': response_on_python['fiscalDocNum'],
            'fiscal_sign': response_on_python['fiscalSign']
        }
        return res
    else:
        return False