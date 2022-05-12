import win32com.client
import pythoncom
from loggings import w_loggings
from setting import settings
import datetime
from time import sleep


def Inc_to_shtih_TAX_SYSTEM(tax_system):
    """Перевод значения в число кода системы налогообложения Штрих"""
    shtrih_tax_system_dict = {
        '0': 1,  # ОСН
        '1': 2,  # УСН Д
        '2': 4,  # УСН Д-Р
        '4': 16,  # ЕСХН
        '5': 32  # ПСН
    }
    if tax_system in shtrih_tax_system_dict.keys():
        return shtrih_tax_system_dict[tax_system]
    else:
        w_loggings(f"Ошибочное значение системы налогообложения{tax_system} для кассы Штрих")
        return False


def Inc_to_shtih_TAX_CODE(tax_code):
    """Перевод значения в число кода ставки НДС Штрих"""
    shtrih_tax_code_dict = {
        1: 1,  # НДС 20%
        2: 2,  # НДС 10%
        5: 3,  # НДС 0%
        6: 0  # Без НДС
    }
    if tax_code in shtrih_tax_code_dict.keys():
        return shtrih_tax_code_dict[tax_code]
    else:
        w_loggings(f"Ошибочное значение ставки НДС {tax_code} для кассе Штрих")
        return False


def shtrih_open_session():
    """Инициализация драйвера создание объекта кассы проверка связи"""
    # подключение объекта драйвера
    pythoncom.CoInitialize()
    fr = win32com.client.Dispatch("Addin.DrvFR")
    fr.ConnectionType = settings.CON_TYPE  # тип подключения 6- TCP Сокет 0- СОМ
    fr.IPAddress = settings.IP_ADRESS
    fr.ComNumber = settings.COM
    fr.BaudRate = 6  # скорость 115200
    fr.UseIPAddress = True  # Используем свойство IPAddress
    fr.password = 30
    fr.Timeout = settings.TIMEOUT
    fr.TCPPort = settings.TCPPORT
    if fr.Connect() != 0:  # Проверяем подключение
        w_loggings(f"Ошибка подключения к кассе Штрих {fr.ResultCode} : {fr.ResultCodeDescription}")
        return False
    w_loggings(f"Соединение установлено с кассой Штрих на адрес {settings.IP_ADRESS}")
    return fr


def shtrih_close_session(fr):
    """Закрытие сеанса работы с кассой Штрих"""
    fr.Disconnect()
    pythoncom.CoUninitialize()
    w_loggings("Соединение с кассой Штрих прервано")


def shtrih_get_status():
    """ Запрос статуса на кассе Штрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    res = {}
    if shtrih_kkt:
        # Статус ФН
        if shtrih_kkt.FNGetStatus() != 0:
            w_loggings(f"Ошибка запроса статуса ФН {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
        else:
            res['fn_number'] = shtrih_kkt.SerialNumber
            res['shft_isopen'] = True if shtrih_kkt.FNSessionState == 1 else False
        # Запрос статуса смены на кассе
        if shtrih_kkt.FNGetCurrentSessionParams() != 0:
            w_loggings(f"Ошибка запроса статуса смены штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
        else:
            res['shft_num'] = shtrih_kkt.SessionNumber
        # Запрос статуса кассы
        if shtrih_kkt.GetECRStatus() != 0:
            w_loggings(f"Ошибка запроса статуса касы штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
        else:
            res['is24Expired'] = True if shtrih_kkt.ECRMode == 3 else False
            res['date_time'] = f"{datetime.datetime.strftime(shtrih_kkt.Date, '%Y-%m-%d')}T{shtrih_kkt.TimeStr}"
            if shtrih_kkt.ECRMode == 8:
                shtrih_kkt.CancelCheck()
                sleep(2)
        shtrih_close_session(shtrih_kkt)
        return res
    else:
        return False


def shtrih_open_shift(kkt):
    """ Открытие смены на кассе Штрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    res = {}
    if shtrih_kkt:
        # Программирование кассира в таблице 2 кассы ряд 2 пароль 2
        shtrih_kkt.TableNumber = 2
        shtrih_kkt.RowNumber = 2
        shtrih_kkt.FieldNumber = 2
        shtrih_kkt.ValueOfFieldString = f"{kkt.cashier_name[:64]}"
        if shtrih_kkt.WriteTable() != 0:
            w_loggings(
                f"Ошибка записи таблица - 2 : ФИО кассира  штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_close_session(shtrih_kkt)
            return False
        # Программирование ИНН кассира в таблице 18 кассы ряд 23
        shtrih_kkt.TableNumber = 18
        shtrih_kkt.RowNumber = 1
        shtrih_kkt.FieldNumber = 23
        shtrih_kkt.ValueOfFieldString = f"{kkt.cashier_inn[:13]}"
        if shtrih_kkt.WriteTable() != 0:
            w_loggings(
                f"Ошибка записи таблица - 18 : ИНН кассира штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_close_session(shtrih_kkt)
            return False
        # Программирование реквизита печати чека в таблице 17 кассы поле 7
        if settings.PRINT_DOC == False:
            shtrih_kkt.TableNumber = 17
            shtrih_kkt.RowNumber = 1
            shtrih_kkt.FieldNumber = 7
            shtrih_kkt.ValueOfFieldString = 1
            if shtrih_kkt.WriteTable() != 0:
                w_loggings(
                    f"Ошибка записи таблица - 17 : печать чека штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
                shtrih_close_session(shtrih_kkt)
                return False
        # Открытие смены оператором 2
        shtrih_kkt.password = 2
        if shtrih_kkt.FNOpenSession() != 0:
            w_loggings(
                f"Ошибка открытия смены на кассе штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_close_session(shtrih_kkt)
            return False
        # ожидание выхода чека открытия смены
        sleep(5)
        # Запрос статуса смены на кассе
        shtrih_kkt.password = 30
        if shtrih_kkt.FNGetCurrentSessionParams() != 0:
             w_loggings(
                 f"Ошибка запроса статуса смены штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
             shtrih_close_session(shtrih_kkt)
             return False
        else:
            res['shft_num'] = shtrih_kkt.SessionNumber
            w_loggings(
                f"На кассе штрих открыта смена {res['shft_num']}")
            shtrih_close_session(shtrih_kkt)
            return res
    return False


def shtrih_close_shift(kkt):
    """ Закрытие смены на кассе Штрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    res = {}
    if shtrih_kkt:
        # Программирование реквизита печати чека в таблице 17 кассы поле 7
        if settings.PRINT_DOC == False:
            shtrih_kkt.TableNumber = 17
            shtrih_kkt.RowNumber = 1
            shtrih_kkt.FieldNumber = 7
            shtrih_kkt.ValueOfFieldString = 1
            if shtrih_kkt.WriteTable() != 0:
                w_loggings(
                    f"Ошибка записи таблица - 17 : печать чека штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
                shtrih_close_session(shtrih_kkt)
                return False
        # Закрытие смены оператором 30
        shtrih_kkt.password = 30
        if shtrih_kkt.FNCloseSession() != 0:
            w_loggings(
                f"Ошибка закрытия смены на кассе штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_close_session(shtrih_kkt)
            return False
        # ожидание выхода чека закрытия смены
        sleep(5)
        # Запрос статуса смены на кассе
        shtrih_kkt.password = 30
        if shtrih_kkt.FNGetCurrentSessionParams() != 0:
             w_loggings(
                 f"Ошибка запроса статуса смены штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
             shtrih_close_session(shtrih_kkt)
             return False
        else:
            res['shft_num'] = shtrih_kkt.SessionNumber
            w_loggings(
                f"На кассе штрих закрыта смена {res['shft_num']}")
            shtrih_close_session(shtrih_kkt)
            return res
    return False


def shtrih_open_check(kkt, check_kkt, check_type=0):
    """Открытие чека на кассе Штрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    if shtrih_kkt:
        # Программирование реквизита печати чека в таблице 17 кассы поле 7
        if settings.PRINT_DOC == False:
            shtrih_kkt.TableNumber = 17
            shtrih_kkt.RowNumber = 1
            shtrih_kkt.FieldNumber = 7
            shtrih_kkt.ValueOfFieldString = 1
            if shtrih_kkt.WriteTable() != 0:
                w_loggings(
                    f"Ошибка записи таблица - 17 : печать чека штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
                shtrih_close_session(shtrih_kkt)
                return False
        # Открытие смены оператором 2
        shtrih_kkt.password = 2
        # Определение типа чека
        shtrih_kkt.CheckType = 1 if check_type == 0 else 3
    return True


def shtrih_add_goods(kkt, check_kkt):
    """ Добавление товаров в чек на кассе Штрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    if shtrih_kkt:
        for good in check_kkt.goods:
            shtrih_kkt.Password = 2
            shtrih_kkt.Price = good['price'] / 100
            shtrih_kkt.Quantity = good['qty'] / 10000
            shtrih_kkt.Summ1Enabled = False
            shtrih_kkt.TaxValueEnabled = False
            shtrih_kkt.Department = 1
            shtrih_kkt.Tax1 = Inc_to_shtih_TAX_CODE(good['tax_code'])

            shtrih_kkt.PaymentItemSign = good['product_type_code']
            shtrih_kkt.StringForPrinting = good['product_name']
            if shtrih_kkt.FNOperation() != 0:
                w_loggings(
                    f"Ошибка добавления позиции в чек кассы штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
                return False
        return True
    return False


def shtrih_close_check(kkt, check_kkt):
    """ Закрытие чека на кассе Щтрих"""
    shtrih_kkt = shtrih_open_session()
    # Если есть соединение с кассой
    if shtrih_kkt:
        shtrih_kkt.Password = 2
        # Вычисление сумм оплаты наличными
        if check_kkt.cash != 0:
            shtrih_kkt.Summ1 = check_kkt.cash / 100
        else:
            shtrih_kkt.Summ1 = 0
        # Вычисление суммы оплаты безналичными
        if check_kkt.ecash != 0:
            shtrih_kkt.CheckSubTotal()
            if check_kkt.ecash / 100 >= shtrih_kkt.Summ1:
                shtrih_kkt.Summ2 = shtrih_kkt.Summ1
                shtrih_kkt.Summ1 = 0
            else:
                shtrih_kkt.Summ2 = check_kkt.ecash / 100
                shtrih_kkt.Summ1 = shtrih_kkt.Summ1 - shtrih_kkt.Summ2
        else:
            shtrih_kkt.Summ2 = 0
        # Определяем систему налогообложения чека
        shtrih_kkt.TaxType = Inc_to_shtih_TAX_SYSTEM(check_kkt.tax_system)
        # Заполнение ТЭГа отправки чека покупателю на электронный адрес
        if check_kkt.send_check_to != '':
            shtrih_kkt.CustomerEmail = check_kkt.send_check_to
            if shtrih_kkt.FNSendCustomerEmail() != 0:
                w_loggings(
                    f"Ошибка записи тега 1008  {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
                shtrih_close_session(shtrih_kkt)
                return False
        # Заполнение данных о покупателе в чек
        if check_kkt.buyer_name != '':
            shtrih_kkt.TagNumber = 1227
            shtrih_kkt.TagType = 7
            shtrih_kkt.TagValueStr = check_kkt.buyer_name
            if shtrih_kkt.FNSendTag() != 0:
                w_loggings(
                    f"Ошибка записи тега 1227  {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_kkt.TagNumber = 1228
            shtrih_kkt.TagType = 7
            shtrih_kkt.TagValueStr = check_kkt.buyer_inn
            shtrih_kkt.FNSendTag()
    # Закрываем чек
        if shtrih_kkt.FNCloseCheckEx() != 0:
            # Ошибка закрытия чека
            w_loggings(
                    f"Ошибка  закрытия чека кассы штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
            shtrih_close_session(shtrih_kkt)
            return False
        sleep(2)
        res = {
            'fiscal_doc_num': shtrih_kkt.DocumentNumber,
            'fiscal_sign': shtrih_kkt.FiscalSignAsString
        }
        # Получение данных о номере чека и дате времени в смене по номеру фискального документа
        shtrih_kkt.password = 30
        shtrih_kkt.DocumentNumber = res['fiscal_doc_num']
        if shtrih_kkt.FNFindDocument() != 0:
            w_loggings(
                f"Ошибка  получения данных чека кассы штрих {shtrih_kkt.ResultCode}:{shtrih_kkt.ResultCodeDescription}")
            return False
        res['date_time'] = f"{datetime.datetime.strftime(shtrih_kkt.Date, '%Y-%m-%d')}T" \
                           f"{datetime.datetime.strftime(shtrih_kkt.Time, '%H:%M')}"
        # Запрос статуса смены на кассе
        if shtrih_kkt.FNGetCurrentSessionParams() != 0:
            w_loggings(
                f"Ошибка запроса статуса смены штрих {shtrih_kkt.ResultCode} : {shtrih_kkt.ResultCodeDescription}")
        else:
            res['shft_num'] = shtrih_kkt.SessionNumber
            res['check_num'] = shtrih_kkt.ReceiptNumber
        w_loggings(f"Закрытие чека № {res['check_num']} на кассе {res['date_time']}")
        shtrih_close_session(shtrih_kkt)
        return res
    return False
