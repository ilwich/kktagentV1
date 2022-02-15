"""Модуль описания основных классов"""
from setting import settings
import datetime
from incerman_exchange import inc_open_session, inc_close_session, inc_get_status, inc_open_shift, inc_close_shift, \
    inc_open_check, inc_add_goods, inc_close_check
from loggings import w_loggings


class Kkt:
    """Описание кассы"""
    def __init__(self, inn_kkt, fn_number, cashier_name, cashier_inn):
        self.inn_kkt = inn_kkt
        self.fn_number = fn_number
        self.cashier_name = cashier_name
        self.cashier_inn = cashier_inn
        self.session_key = '0'
        self.shft_num = '0'

    def __str__(self):
        return f'На кассе ИНН пользователя {self.inn_kkt} с ФН {self.fn_number} смена {self.shft_num} '


    def to_json(self):
        """ Представление класса KKT в JSON"""
        return {'kkt': { 'inn_kkt': self.inn_kkt,
                         'fn_number': self.fn_number,
                         'cashier_name': self.cashier_name,
                         'cashier_inn': self.cashier_inn
                         }
                }

    def open_shft(self):
        """Открытие смены на кассе"""
        if settings.KKT_MODEL == 'Incotex':
            if self.session_key == '0':
                self.session_key = inc_open_session()
            if self.session_key != '0':
                kkt_status = inc_get_status(self.session_key)
                if kkt_status:
                    if kkt_status['fn_number'] == self.fn_number:
                        shft_status = {'shft_num': kkt_status['shft_num']}
                        if not kkt_status['shft_isopen'] and not kkt_status['is24Expired']:
                            shft_status = inc_open_shift(self.session_key, self)
                        elif kkt_status['shft_isopen'] and kkt_status['is24Expired']:
                            shft_status = inc_close_shift(self.session_key, self)
                            if shft_status:
                                shft_status = inc_open_shift(self.session_key, self)
                        self.shft_num = shft_status['shft_num']
                        return True
                    else:
                        w_loggings(f'Номер ФН в кассе {kkt_status["fn_number"]} не соответствует ФН на сервере {self.fn_number}')
                        return False
            else:
                return False
            if inc_close_session(self.session_key):
                self.session_key = '0'

    def close_shft(self):
        """Закрытие смены на кассе"""
        if settings.KKT_MODEL == 'Incotex':
            if self.session_key == '0':
                self.session_key = inc_open_session()
            if self.session_key != '0':
                kkt_status = inc_get_status(self.session_key)
                if kkt_status['fn_number'] == self.fn_number:
                    shft_status = {'shft_num': kkt_status['shft_num']}
                    if kkt_status['shft_isopen']:
                        shft_status = inc_close_shift(self.session_key, self)
                    if shft_status:
                        self.shft_num = shft_status['shft_num']
                else:
                    w_loggings(f'Номер ФН в кассе {kkt_status["fn_number"]} не соответствует ФН на сервере {self.fn_number}')
            if inc_close_session(self.session_key):
                self.session_key = '0'

    def make_check_onbuy(self, check_kkt):
        """Проведение чека прихода"""
        if settings.KKT_MODEL == 'Incotex':
            if self.session_key == '0':
                self.session_key = inc_open_session()
            if self.session_key != '0':
                check_status = 0
                if inc_open_check(self.session_key, self, check_kkt, 0):
                    for good in check_kkt.goods:
                        inc_add_goods(self.session_key, self, good)
                check_status = inc_close_check(self.session_key, self, check_kkt)
                if check_status:
                    # Забираем текущую дату время чека из кассы для формирования qr кода в строку статуса
                    check_date_time = inc_get_status(self.session_key)['date_time']
                    check_kkt.shft_num = check_status['shft_num']
                    check_kkt.check_num = check_status['check_num']
                    # формирование  строки данных для qr кода чека
                    check_datetime = datetime.datetime.strptime(check_date_time, '%Y-%m-%dT%H:%M:%S').strftime(
                        "%Y%m%dT%H%M")
                    check_summ = (check_kkt.cash + check_kkt.ecash) / 100
                    data = f"t={check_datetime}" \
                           f"&s={check_summ:.02f}" \
                           f"&fn={self.fn_number}" \
                           f"&i={check_status['fiscal_doc_num']}" \
                           f"&fp={check_status['fiscal_sign']}&n=1"
                    check_kkt.status = data
            if inc_close_session(self.session_key):
                self.session_key = '0'
                return True
        return False


class Check:
    """Описание чека"""
    def __init__(self, date_added, buyer_name='', buyer_inn='', tax_system='0', send_check_to='info@5element35.ru',
                     cash=0, ecash=0, status='Добавлен'):
            # номер смены
            self.shft_num = 0
            # номер чека
            self.check_num = 0
            # наименование покупателя
            self.buyer_name = buyer_name
            # ИНН покупателя
            self.buyer_inn = buyer_inn
            # Система налогообложения
            self.tax_system = tax_system
            # Адрес отправки чека
            self.send_check_to = send_check_to
            # Оплата наличными
            self.cash = cash
            # Оплата безналичными
            self.ecash = ecash
            self.status = status
            self.date_added = date_added
            # Список товаров в чек
            self.goods = []

    def to_json(self):
        """ Представление класса Check в JSON"""
        return {'check': {
            'shft_num': self.shft_num,
            'check_num': self.check_num,
            'buyer_name': self.buyer_name,
            'buyer_inn': self.buyer_inn,
            'tax_system': self.tax_system,
            'send_check_to': self.send_check_to,
            'cash': self.cash,
            'ecash': self.ecash,
            'status': self.status,
            'date_added': self.date_added
        }
        }

    def __str__(self):
        return f"Чек {self.check_num} в смене {self.shft_num} дата {self.date_added} имеет статус {self.status}"

    def uptodate(self, shft_num=None, check_num=None, buyer_name=None, buyer_inn=None, tax_system=None,
                     send_check_to=None, status=None, cash=None, ecash=None):
        """Обновление полей класса Check"""
        if shft_num != None:
            self.shft_num = shft_num
        if check_num != None:
            self.check_num = check_num
        if buyer_name != None:
            self.buyer_name = buyer_name
        if buyer_inn != None:
            self.buyer_inn = buyer_inn
        if tax_system != None:
            self.tax_system = tax_system
        if send_check_to != None:
            self.send_check_to = send_check_to
        if status != None:
            self.status = status
        if cash != None:
            self.cash = cash
        if ecash != None:
            self.ecash = ecash
