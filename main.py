from server_exchange import get_token, get_kkt, get_kkt_detail, uptodate_kkt, get_check_info,\
    get_check_detail, uptodate_kkt_check
from incerman_exchange import inc_get_drvinfo, inc_open_session, inc_close_session, inc_get_status, inc_open_shift,\
    inc_close_shift
from models import Kkt, Check, w_loggings
from setting import settings
from time import sleep
import requests
from icecream import ic
from loggings import w_loggings



if __name__ == '__main__':
    fn_number = settings.FN_NUMBER
    if get_token():                 # Если удачно получен токен от сервера по имени и паролю
        k = get_kkt_detail(fn_number)   # По номеру ФН получаем информацию о кассе
        while True:
            chk_arr = get_check_info(fn_number)  # Запрос добавленных чеков
            if chk_arr:
                if k.open_shft():                   # Открытие смены на локальном кассовом аппарате
                    for el in chk_arr:
                        get_check_detail(k, el)          # Запрос подробной информации по чекам
                        check_status = k.make_check_onbuy(el)       # Регистрация чека на кассовом аппарате
                        if check_status:
                             uptodate_kkt_check(k, el)          # Обновление информации о чеке на сервере
            sleep(settings.TIMER)






    # print(inc_get_drvinfo())
    # k.session_key = inc_open_session()
    # ic(k.session_key)
    # if k.session_key:
    #     kkt_status = inc_get_status(k.session_key)
    #     ic(kkt_status)
    #     if kkt_status['fn_number'] == fn_number:
    #         if not kkt_status['shft_isopen'] and not kkt_status['is24Expired']:
    #             shft_status = inc_open_shift(k.session_key, k)
    #         elif kkt_status['shft_isopen'] and kkt_status['is24Expired']:
    #             shft_status = inc_close_shift(k.session_key, k)
    #             if shft_status:
    #                 shft_status = inc_open_shift(k.session_key, k)
    #         w_loggings(f"СМена открыта {kkt_status['shft_num']}")
    #         shft_status = inc_close_shift(k.session_key, k)
    #         print(inc_close_session(k.session_key))









# See PyCharm help at https://www.jetbrains.com/help/pycharm/
