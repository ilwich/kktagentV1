"""Модуль обмена с кассами Атол"""
import requests
from time import sleep
from loggings import w_loggings
from setting import settings
from base64 import b64encode
from libfptr10 import IFptr


def Inc_to_atol_TAX_SYSTEM(tax_system):
    """Перевод в строковые константы кода системы налогообложения АТОЛ"""
    atol_tax_system_dict = {
        '0': IFptr.LIBFPTR_TT_OSN,
        '1': IFptr.LIBFPTR_TT_USN_INCOME,
        '2': IFptr.LIBFPTR_TT_USN_INCOME_OUTCOME,
        '4': IFptr.LIBFPTR_TT_ESN,
        '5': IFptr.LIBFPTR_TT_PATENT
    }
    if tax_system in atol_tax_system_dict.keys():
        return atol_tax_system_dict[tax_system]
    else:
        w_loggings(f"Ошибочное значение системы налогообложения{tax_system} для кассы АТОЛ")
        return False


def atol_open_session():
    """Инициализация драйвера создание объекта кассы проверка связи"""
    fptr = IFptr("")
    if settings.ATOL_CON_TYPE == 6:
        atol_settings = "{{\"{}\": {}, \"{}\": {}, \"{}\": \"{}\", \"{}\": {}}}".format(
            IFptr.LIBFPTR_SETTING_MODEL, IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT, IFptr.LIBFPTR_PORT_TCPIP,
            IFptr.LIBFPTR_SETTING_IPADDRESS, settings.ATOL_IP_ADRESS,
            IFptr.LIBFPTR_SETTING_IPPORT, settings.ATOL_IP_PORT)
    if settings.ATOL_CON_TYPE == 0:
        atol_settings = "{{\"{}\": {}, \"{}\": {}, \"{}\": \"{}\", \"{}\": {}}}".format(
            IFptr.LIBFPTR_SETTING_MODEL, IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT, IFptr.LIBFPTR_PORT_COM,
            IFptr.LIBFPTR_SETTING_COM_FILE, settings.ATOL_PORT,
            IFptr.LIBFPTR_SETTING_BAUDRATE, IFptr.LIBFPTR_PORT_BR_115200)
    fptr.setSettings(atol_settings)
    try_count = 0
    while try_count < settings.INC_TRY_COUNT:
        # Установка соединения с ККТ
        try:
            fptr.open()
            if fptr.isOpened() == 1:
                w_loggings(f"Соединение установлено с кассой АТОЛ на порт {settings.ATOL_PORT}")
                return fptr
        except:
            w_loggings(f"Ошибка подключения к драйверу АТОЛ")
        try_count += 1
    w_loggings(f"Ошибка кассы атол. Соединение не установлено с кассой АТОЛ на порт {settings.ATOL_PORT}")
    return False


def atol_close_session(fptr):
    """Закрытие сеанса работы с кассой АТОЛ"""
    fptr.close()
    w_loggings("Соединение с кассой Атол прервано")


def atol_reset_check(fptr):
    """Отмена незаконченного документа на кассе атол"""
    fptr.cancelReceipt()
    w_loggings(f"Отмена текущего документа на кассе атол")
    return fptr

def atol_operator_login(fptr, kkt):
    """Регистрация ператора на кассе АТОЛ"""
    fptr.setParam(1021, f"Кассир {kkt.cashier_name}")
    fptr.setParam(1203, f"{kkt.cashier_inn}")
    fptr.operatorLogin()
    return fptr


def atol_get_status():
    """ Запрос статуса на кассы АТОЛ"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
        if atol_kkt.fnQueryData() == 0:
            fn_number = atol_kkt.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        else:
            w_loggings("Ошибка кассы атол. Код {} [{}]".format(atol_kkt.errorCode(), atol_kkt.errorDescription()))
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        if atol_kkt.queryData() == 0:
            shft_num = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            shft_status = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
            date_time = atol_kkt.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).strftime('%Y-%m-%dT%H:%M:%S')
            receipt_type = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
        else:
            w_loggings("Ошибка кассы атол. Код {} [{}]".format(atol_kkt.errorCode(), atol_kkt.errorDescription()))
        atol_kkt.close()
        w_loggings(f"Получены данные о статусе кассы атол с фн {fn_number}")
        res = {'fn_number': fn_number, 'shft_num': shft_num, 'date_time': date_time,
               'is24Expired': True if shft_status == atol_kkt.LIBFPTR_SS_EXPIRED else False,
               'shft_isopen': True if shft_status == atol_kkt.LIBFPTR_SS_OPENED else False}
        # Если чек не закрыт, то подождать и провести отмену
        if receipt_type != 0:
            sleep(20)
            atol_reset_check(atol_kkt)
        return res
    return False


def atol_open_shift(kkt):
    """ Открытие смены на кассе АТОЛ"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        atol_operator_login(atol_kkt, kkt)
        # отключение печати чека отчета открытия
        if settings.PRINT_DOC == False:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, True)
        atol_kkt.openShift()
        if atol_kkt.checkDocumentClosed() < 0:
            # Смена не открылась.
            w_loggings("Ошибка открытия смены на кассе атол. ")
            return False
        # Получение номера смены
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        if atol_kkt.queryData() == 0:
            shft_num = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            w_loggings(f"Открыта смена № {shft_num} на кассе {kkt.fn_number}")
            res = {
                'shft_num': shft_num
            }
            atol_close_session(atol_kkt)
            return res
        else:
            w_loggings(f"Не удалось получить номер смены на кассе Атол {kkt.fn_number}")
            return False
    else:
        return False


def atol_close_shift(kkt):
    """ Закрытие смены на кассе АТОЛ"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        # регистрация кассира в чеке
        atol_operator_login(atol_kkt, kkt)
        # отключение печати чека отчета открытия
        if settings.PRINT_DOC == False:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, True)
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
        atol_kkt.report()
        if atol_kkt.checkDocumentClosed() < 0:
            # Смена не закрылась
            w_loggings("Ошибка закрытие смены на кассе атол. ")
            return False
        # Получение номера смены
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        if atol_kkt.queryData() == 0:
            shft_num = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            w_loggings(f"Закрытие смены № {shft_num} на кассе {kkt.fn_number}")
            res = {
                'shft_num': shft_num
            }
            atol_close_session(atol_kkt)
            return res
        else:
            w_loggings(f"Не удалось получить номер смены на кассе Атол {kkt.fn_number}")
            return False
    else:
        return False


def atol_open_check(kkt, check_kkt, check_type=0):
    """ Открытие чека на кассе АТОЛ"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        # регистрация кассира в чеке
        atol_operator_login(atol_kkt, kkt)
        # добавить информацию о покупателе в чек
        if check_kkt.buyer_name != '':
            atol_kkt.setParam(1227, check_kkt.buyer_name)
            atol_kkt.setParam(1228, check_kkt.buyer_inn)
        # тип чека прихода
        if check_type == 0:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL)
        # отключение печати чека
        if settings.PRINT_DOC == False:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
        if check_kkt.send_check_to != '':
            atol_kkt.setParam(1008, check_kkt.send_check_to)
        if Inc_to_atol_TAX_SYSTEM(check_kkt.tax_system):
            atol_kkt.setParam(1055, Inc_to_atol_TAX_SYSTEM(check_kkt.tax_system))
        atol_kkt.openReceipt()
        w_loggings(f"Открыт чек на кассе {kkt.fn_number}")
        return True
    else:
        w_loggings(f"Ошибка открытия чека ")
        return False


def atol_add_goods(kkt, good):
    """ Добавление товаров в чек на кассе Атол"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, good['product_name'])
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_PRICE, good['price'] / 100)
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, good['qty'] / 10000)
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, good['tax_code'])
        atol_kkt.setParam(1212, good['product_type_code'])
        atol_kkt.registration()
        w_loggings(f"Добавлен товар {good['product_name']} на кассе {kkt.fn_number}")
        return True
    else:
        return False


def atol_close_check(kkt, check_kkt):
    """ Закрытие чека на кассе Атол"""
    atol_kkt = atol_open_session()
    # Если есть соединение с кассой
    if atol_kkt:
        if check_kkt.cash != 0:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_kkt.cash / 100)
        if check_kkt.ecash != 0:
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_kkt.ecash / 100)
        atol_kkt.payment()
        atol_kkt.closeReceipt()
        if atol_kkt.checkDocumentClosed() < 0:
            # Ошибка закрытия чека
            w_loggings(f"Ошибка  закрытия чека {atol_kkt.errorDescription()}.")
            return False
        sleep(2)
        atol_kkt.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
        if atol_kkt.fnQueryData() == 0:
            res = {
                'fiscal_doc_num': atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
                'fiscal_sign': atol_kkt.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN),
                'date_time': atol_kkt.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
            }
            w_loggings(f"Закрытие чека № {res['fiscal_doc_num']} на кассе {res['dateTime']}")
            # Получение номера смены
            atol_kkt.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
            if atol_kkt.queryData() == 0:
                res['shft_num'] = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
                atol_kkt.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
                if atol_kkt.queryData() == 0:
                    res['check_num'] = atol_kkt.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER)
                atol_close_session(atol_kkt)
                return res
        else:
            w_loggings(f"Не удалось зарегистрировать чек на кассе Атол {kkt.fn_number}")
    return False
