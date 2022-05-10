"""Модуль обмена с сервером Инкотекса"""
import requests
from time import sleep
from models import *
from loggings import w_loggings
from setting import settings
from base64 import b64encode


def num_into_one_byte(num):
    """Возвражает число с одним битом в позиции num"""
    byte_num = 1
    for _ in range(num):
        byte_num = byte_num << 1
    return byte_num


def armax_get_status():
    """Получение статуса кассы АРМАКС"""
    username = settings.ARMAX_LOGIN
    password = settings.ARMAX_PASS
    userAndPass = b64encode(bytes(username + ':' + password, "utf-8")).decode("ascii")
    headers = {'Authorization': 'Basic %s' % userAndPass,
               'Content-type': 'application/json; charset=utf-8',
               }
    url = settings.URL_ARMAX + f'/cashboxstatus.json'  # Полный адрес до кассы запрос состояния
    response = ''
    while response == '':
        try:
            response = requests.get(url, headers=headers)  # Делаем GET-запрос
            break
        except:
            w_loggings(f"Касса не отвечает по адресу {settings.URL_ARMAX}...")
            sleep(5)
            continue
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if 'result' not in response_on_python:
        w_loggings(f"Получены данные о статусе кассы {response_on_python['cashboxStatus']['fsNumber']}")
        res = {'fn_number': response_on_python['cashboxStatus']['fsNumber'],
               'shft_num': response_on_python['cashboxStatus']['cycleNumber'],
               'date_time': response_on_python['cashboxStatus']['dt'],
               'inn_kkt': response_on_python['cashboxStatus']['userInn'],
               'is24Expired': False}
        # Смена по умолчанию не закончена. Касса автоматически сама может переоткрывать смену
        if (response_on_python['cashboxStatus']['flags'] & 2) == 2:
            res['shft_isopen'] = True
        else:
            res['shft_isopen'] = False
        return res
    else:
        w_loggings(f"Ошибка {response_on_python['result']} получения статуса кассы {response_on_python['message']}")
        return False


def armax_open_shift(kkt):
    """ Открытие смены на кассе сервера armax"""
    username = settings.ARMAX_LOGIN
    password = settings.ARMAX_PASS
    userAndPass = b64encode(bytes(username + ':' + password, "utf-8")).decode("ascii")
    headers = {'Authorization': 'Basic %s' % userAndPass,
               'Content-type': 'application/json; charset=utf-8',
               }
    # параметр печати чека
    print_doc = 1 if settings.PRINT_DOC else 0
    url = settings.URL_ARMAX + f'/cycleopen.json?print={print_doc}'  # Полный адрес до кассы запрос состояния
    response = ''
    while response == '':
        try:
            response = requests.get(url, headers=headers)  # Делаем GET-запрос
            break
        except:
            w_loggings(f"Касса не может открыть смену {settings.URL_ARMAX}...")
            sleep(5)
            continue
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['document']['result'] == 0:
        data_from_kkt = response_on_python['document']['data']['fiscprops']
        for tag in data_from_kkt:
            if tag['tag'] == 1038:
                w_loggings(f"Открыта смена № {tag['value']} на кассе {kkt.fn_number}")
                res = {
                    'shft_num': tag['value']
                }
        return res
    else:
        w_loggings(f"Ошибка {response_on_python['document']['result']} откытия смены {response_on_python['message']}")
        return False


def armax_close_shift(kkt):
    """ Закрытие смены на кассе Armax"""
    username = settings.ARMAX_LOGIN
    password = settings.ARMAX_PASS
    userAndPass = b64encode(bytes(username + ':' + password, "utf-8")).decode("ascii")
    headers = {'Authorization': 'Basic %s' % userAndPass,
               'Content-type': 'application/json; charset=utf-8',
               }
    # параметр печати чека
    print_doc = 1 if settings.PRINT_DOC else 0
    url = settings.URL_ARMAX + f'/cycleclose.json?print={print_doc}'  # Полный адрес до кассы запрос состояния
    response = ''
    while response == '':
        try:
            response = requests.get(url, headers=headers)  # Делаем GET-запрос
            break
        except:
            w_loggings(f"Касса не может закрыть смену {settings.URL_ARMAX}...")
            sleep(5)
            continue
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['document']['result'] == 0:
        data_from_kkt = response_on_python['document']['data']['fiscprops']
        for tag in data_from_kkt:
            if tag['tag'] == 1038:
                w_loggings(f"Закрыта смена № {tag['value']} на кассе {kkt.fn_number}")
                res = {
                    'shft_num': tag['value']
                }
        return res
    else:
        w_loggings(f"Ошибка {response_on_python['document']['result']} закрытия смены {response_on_python['message']}")
        return False


def armax_make_check(kkt, check_kkt, check_type=1):
    """ Фискализация чека на кассе Armax"""
    username = settings.ARMAX_LOGIN
    password = settings.ARMAX_PASS
    userAndPass = b64encode(bytes(username + ':' + password, "utf-8")).decode("ascii")
    headers = {'Authorization': 'Basic %s' % userAndPass,
               'Content-type': 'application/json; charset=utf-8',
               }
    # параметр печати чека
    print_doc = 1 if settings.PRINT_DOC else 0
    url = settings.URL_ARMAX + f'/fiscalcheck.json'  # Полный адрес до кассы запрос состояния
    data = {'document': {
        'sessionId': datetime.datetime.fromisoformat(check_kkt.date_added[:-4]).strftime("%Y%m%d%H%M"),
        'print': print_doc,
        'data': {
            'type': check_type,  # Тип документа 1 - ПРИХОД
            'fiscprops': [
                {
                    'tag': 1055,  # Код системы налогообложения в битовом биде
                    'value': num_into_one_byte(int(check_kkt.tax_system))
                },
                {
                    'tag': 1054,  # Тип документа 1 - приход
                    'value': check_type
                },
                {
                    'tag': 1008,  # Адрес получателя чека
                    'value': check_kkt.send_check_to
                },
                {
                    'tag': 1021,  # ФИО кассир
                    'value': kkt.cashier_name
                },
                {
                    'tag': 1203,  # ИНН кассир
                    'value': kkt.cashier_inn
                },
                {
                    'tag': 1031,  # Сумма по чеку наличными
                    'value': check_kkt.cash
                },
                {
                    'tag': 1081,  # Сумма по чеку безналичными
                    'value': check_kkt.ecash
                }
            ]
        }
    }}
    # Добавление данных о покупателе в чек
    if check_kkt.buyer_name != '':
        data['document']['data']['fiscprops'].extend([{
            'tag': 1227,  # Название покупателя
            'value': check_kkt.buyer_name
        },
            {
                'tag': 1228,  # ИНН Покупателя
                'value': check_kkt.buyer_inn
            }])

    for good in check_kkt.goods:
        fiscprops = [
            {
                'tag': 1214,  # признак способа расчета
                'value': 4  # 4 - полная оплата
            },
            {
                'tag': 1212,  # признак предмета расчета
                'value': good['product_type_code']
            },
            {
                'tag': 1030,  # наименование
                'value': good['product_name']
            },
            {
                'tag': 1079,  # цена за единицу
                'value': good['price']
            },
            {
                'tag': 1023,  # количество
                'value': "{0:.3f}".format(float(good['qty'] / 10000))
            },
            {
                'tag': 1199,  # ставка НДС
                'value': good['tax_code']
            }]
        data['document']['data']['fiscprops'].append({
            'tag': 1059,  # Добавление позиции
            'fiscprops': fiscprops
        })
    response = requests.post(url, json=data, headers=headers)
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл лог
    if response_on_python['document']['result'] == 0:
        data_from_kkt = response_on_python['document']['data']['fiscprops']
        res = {}
        for tag in data_from_kkt:
            if tag['tag'] == 1042:
                w_loggings(f"Пробит чек № {tag['value']} на кассе {kkt.fn_number}")
                res['check_num'] = tag['value']
            elif tag['tag'] == 1038:  # номер смены
                res['shft_num']= tag['value']
            elif tag['tag'] == 1040:
                res['fiscal_doc_num'] = tag['value']
            elif tag['tag'] == 1077:
                res['fiscal_sign'] = tag['value']
            elif tag['tag'] == 1012:  # время фискализации чека
                res['date_time'] = tag['printable']
        return res
    else:
        w_loggings(
            f"Ошибка {response_on_python['document']['result']} пробития чека {response_on_python['document']['message']['resultDescription']}")
        return False
