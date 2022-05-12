from server_exchange import get_token, get_kkt, get_kkt_detail, uptodate_kkt, get_check_info,\
    get_check_detail, uptodate_kkt_check
from setting import settings, from_json_to_setting
from time import sleep
import servicemanager
import os
import socket
import traceback
import sys
import win32event
import win32service
import win32serviceutil


class KktAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "KktAgentService"
    _svc_display_name_ = "Kkt Agent Service"
    _svc_description_ = "Make exchange from Kassbot.website to KKT"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        rc = None
        while rc != win32event.WAIT_OBJECT_0:
            try:  # try main
                watch_kkt_check()
            except:
                servicemanager.LogErrorMsg(traceback.format_exc())  # if error print it to event log
                os._exit(-1)  # return some value other than 0 to os so that service knows to restart
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)


def watch_kkt_check():
    """Основная процедура опроса сервера для отправки чеков на кассу"""
    from_json_to_setting()
    while True:
        if get_token():  # Если удачно получен токен от сервера по имени и паролю
            k = get_kkt_detail(settings.FN_NUMBER)  # По номеру ФН получаем информацию о кассе
            while True:
                chk_arr = get_check_info(settings.FN_NUMBER)  # Запрос добавленных чеков
                if chk_arr:
                    if k.open_shft():  # Открытие смены на локальном кассовом аппарате
                        for el in chk_arr:
                            get_check_detail(k, el)  # Запрос подробной информации по чекам
                            check_status = k.make_check_onbuy(el)  # Регистрация чека на кассовом аппарате
                            if check_status:
                                uptodate_kkt_check(k, el)  # Обновление информации о чеке на сервере
                sleep(settings.TIMER)
                if from_json_to_setting():
                    break
        else:
            while from_json_to_setting() == False:
                sleep(settings.TIMER)


if __name__ == '__main__':
    #watch_kkt_check()
    if len(sys.argv) == 1:
         servicemanager.Initialize()
         servicemanager.PrepareToHostSingle(KktAgentService)
         servicemanager.StartServiceCtrlDispatcher()
    else:
         win32serviceutil.HandleCommandLine(KktAgentService)

    # if get_token():
    #     kkt_list = get_kkt()
    #     if kkt_list:
    #         for kkt in kkt_list:
    #             print(kkt)
    # fn_number = settings.FN_NUMBER
    # if get_token():  # Если удачно получен токен от сервера по имени и паролю
    #     k = get_kkt_detail(fn_number)  # По номеру ФН получаем информацию о кассе
    #     chk_arr = get_check_info(fn_number)  # Запрос добавленных чеков
    #     if chk_arr:
    #         if k.open_shft():  # Открытие смены на локальном кассовом аппарате
    #             ic(k.to_json())
    #             for el in chk_arr:
    #                  get_check_detail(k, el)  # Запрос подробной информации по чекам
    #                  ic(el.to_json())
    #                  check_status = k.make_check_onbuy(el)  # Регистрация чека на кассовом аппарате
    #                  ic(check_status)
    #                  if check_status:
    #                      uptodate_kkt_check(k, el)  # Обновление информации о чеке на сервере
    #                  else:
    #                      el.status = 'Формируется. Ошибка в чеке!'
    #                      uptodate_kkt_check(k, el)  # Обновление информации о чеке на сервере


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
