"""Модуль обмена с сервером чеков"""
import requests
import time
from models import *
from setting import settings, settings_modify
from loggings import w_loggings


def get_token():
    """Получение токена для API"""
    data = {'username': settings.LOGIN,  # Имя пользователя БД
            'password': settings.PASSWORD
            }
    url = settings.URL + '/api-token-auth/'  # Адрес эндпоинта сервера чеков
    response = requests.post(url, json=data)  # Делаем POST-запрос с данными пользователя
    # Поскольку данные пришли в формате json, переведем их в python
    if response.status_code == 200:
        response_on_python = response.json()
        token_new_val = f"Token {response_on_python['token']}"
        settings_modify(f'TOKEN = ', token_new_val)
        settings.reload()
        return True
    else:
        w_loggings(f'Ошибка авторизации на Сервере чеков {response.status_code}')
        return False


def get_kkt():
    """ Получаем список касс на сервере"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/kkts/'  # Полный адрес эндпоинта
    response = ''
    while response == '':
        try:
            response = requests.get(url, headers=headers)  # Делаем GET-запрос
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as err:
            w_loggings(f"OOps: Something Else {err}")
        except requests.exceptions.HTTPError as errh:
            w_loggings(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            w_loggings(f"Error Connecting:  {errc}")
        except requests.exceptions.Timeout as errt:
            w_loggings(f"Timeout Error:  {errt}")
            time.sleep(5)
            continue
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    # Запишем полученные данные в файл kkt.txt
    res_kkt_arr = []
    for kkt in response_on_python:
        new_kkt = Kkt(kkt['inn_kkt'],
                      kkt['fn_number'],
                      kkt['cashier_name'],
                      kkt['cashier_inn']
                      )
        w_loggings(new_kkt)
        res_kkt_arr.append(new_kkt)

    return res_kkt_arr


def get_kkt_detail(fn_number):
    """Получаем информацию о кассе с сервера по номеру ФН"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/kkt/'  # Полный адрес эндпоинта
    request = ''.join([url, fn_number])
    response = ''
    while response == '':
        try:
            response = requests.get(request, headers=headers)  # Делаем GET-запрос
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as err:
            w_loggings(f"OOps: Something Else {err}")
        except requests.exceptions.HTTPError as errh:
            w_loggings(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            w_loggings(f"Error Connecting:  {errc}")
        except requests.exceptions.Timeout as errt:
            w_loggings(f"Timeout Error:  {errt}")
            time.sleep(5)
            continue

    if response.status_code == 200:
        # Поскольку данные пришли в формате json, переведем их в python
        response_on_python = response.json()
        # Допишем полученные данные в лог
        new_kkt = Kkt(response_on_python['inn_kkt'],
                      response_on_python['fn_number'],
                      response_on_python['cashier_name'],
                      response_on_python['cashier_inn']
                      )
        w_loggings(new_kkt)
    else:
        new_kkt = False
    return new_kkt


def uptodate_kkt(kkt_saved):
    """Обновляем данные о кассе на сервере"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/kkt/'  # Полный адрес эндпоинта
    request = ''.join([url, kkt_saved.fn_number, '/'])
    data = kkt_saved.to_json()
    response = requests.put(request, json=data, headers=headers)
    return response.status_code


def get_check_info(fn_number):
    """Получаем информацию о чеках с сервера по номеру ФН"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/check_kkt/'  # Полный адрес эндпоинта
    request = ''.join([url, fn_number])
    response = ''
    while response == '':
        try:
            response = requests.get(request, headers=headers)  # Делаем GET-запрос
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as err:
            w_loggings(f"OOps: Something Else {err}")
        except requests.exceptions.HTTPError as errh:
            w_loggings(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            w_loggings(f"Error Connecting:  {errc}")
        except requests.exceptions.Timeout as errt:
            w_loggings(f"Timeout Error:  {errt}")
            time.sleep(5)
            continue
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    if response.status_code == 200:
        res = []
        # Допишем полученные данные в файл лог
        for check in response_on_python:
            new_check = Check(
                check['date_added'],
                check['buyer_name'],
                check['buyer_inn'],
                int(check['tax_system']),
                check['send_check_to'],
                int(check['cash']),
                int(check['ecash'])
            )
            w_loggings(new_check)
            res.append(new_check)
    else:
        res = False
    return res


def get_check_detail(kkt, check):
    """Получаем информацию о чеке с сервера по номеру ФН и времени создания чека"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/check_kkt/'  # Полный адрес эндпоинта
    request = ''.join([url, kkt.fn_number, '/', check.date_added])
    response = requests.get(request, headers=headers)  # Делаем GET-запрос
    # Поскольку данные пришли в формате json, переведем их в python
    response_on_python = response.json()
    res = True
    if response.status_code == 200:
        res = response_on_python[0]
        check.uptodate(buyer_inn=res['buyer_inn'], buyer_name=res['buyer_name'], send_check_to=res['send_check_to'],
                       tax_system=res['tax_system'], status=res['status'], cash=res['cash'], ecash=res['ecash']
                       )
        check.goods = []
        for good in res['goods']:
            new_good = {'product_name': good['product_name'],
                        'qty': good['qty'],
                        'tax_code': good['tax_code'],
                        'price': good['price'],
                        'product_type_code': good['product_type_code']
                        }
            check.goods.append(new_good)
        w_loggings(check)
    else:
        res = False
    return res


def uptodate_kkt_check(kkt_saved, check_saved):
    """Обновляем данные о чеке по кассе на сервере"""
    headers = {'Authorization': settings.TOKEN}
    url = settings.URL + '/api/check_kkt/'  # Полный адрес эндпоинта
    request = ''.join([url, kkt_saved.fn_number, '/', check_saved.date_added])
    data = check_saved.to_json()
    response = requests.put(request, json=data, headers=headers)
    return response.status_code
