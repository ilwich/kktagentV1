from dynaconf import Dynaconf
import json

settings = Dynaconf(
    envvar_prefix="DYNACONF",  # export envvars with `export DYNACONF_FOO=bar`.
    settings_files=[
                    'C:\\ProgramData\\V_element\\kktagent\\settings.toml',
#                    'C:\\ProgramData\\V_element\\kktagent\\settings.json',
                    'C:\\ProgramData\\V_element\\kktagent\\.secrets.toml'
                    ],  # Load files in the given order.
)

def from_setting_to_json():
    """Сохранение настроек в файл JSON"""
    set_for_json = {
        'login': settings.LOGIN,
        'password': settings.PASSWORD,
        'kkt_parameters':{
            'kkt_model': settings.KKT_MODEL,
            'fn_number': settings.FN_NUMBER
        },
        'parameters': {
            'timer': settings.TIMER,
            'print_doc': settings.PRINT_DOC
        }
    }
    set_for_json['models'] = []
    set_for_json['models'].append({
        'name': 'Incotex',
        'parameters': {
            'url_incerman': settings.URL_INCERMAN,
            'inc_portname': settings.INC_PORTNAME,
            'inc_try_count': settings.INC_TRY_COUNT
        }
    })
    set_for_json['models'].append({
        'name': 'Shtrih',
        'parameters': {
            'con_type': settings.CON_TYPE,
            'ip_adress': settings.IP_ADRESS,
            'timeout': settings.TIMEOUT,
            'tcpport': settings.TCPPORT,
            'com': settings.COM
        }
    })
    set_for_json['models'].append({
        'name': 'Atol',
        'parameters': {
            'atol_con_type': settings.ATOL_CON_TYPE,
            'atol_port': settings.ATOL_PORT,
            'atol_ip_adress': settings.ATOL_IP_ADRESS,
            'atol_ip_port': settings.ATOL_IP_PORT
        }
    })
    set_for_json['models'].append({
        'name': 'Armax',
        'parameters': {
            'url_armax': settings.URL_ARMAX,
            'armax_login': settings.ARMAX_LOGIN,
            'armax_pass': settings.ARMAX_PASS
        }
    })
    with open('C:\\ProgramData\\V_element\\kktagent\\settings.json', 'w') as outfile:
        json.dump(set_for_json, outfile, sort_keys=True, indent=4)


def settings_modify(setting_str_key, setting_str_val):
    """Изменение строчки с параметром в файле настроек"""
    try:
        with open('C:\\ProgramData\\V_element\\kktagent\\settings.toml', 'r') as setting_file:
            setting_data = setting_file.readlines()
            res = []
            for line in setting_data:
                if line.find(setting_str_key.upper()) == 0:
                    if isinstance(setting_str_val, (bool)):
                        if setting_str_val:
                            res.append(f'{setting_str_key.upper()}true\n')
                        else:
                            res.append(f'{setting_str_key.upper()}false\n')
                    elif isinstance(setting_str_val, (int, float)):
                        res.append(f'{setting_str_key.upper()}{setting_str_val}\n')
                    else:
                        print('OK')

                        res.append(f"{setting_str_key.upper()}'{setting_str_val}'\n")
                else:
                    res.append(line)
    except:
        return False
    if res:
        try:
            with open('C:\\ProgramData\\V_element\\kktagent\\settings.toml', 'w') as setting_file:
                for el in res:
                    setting_file.write(el)
        except:
            return False
    else:
        return False


def from_json_to_setting():
    """Формирование файла настроек из JSON """
    try:
        with open('C:\\ProgramData\\V_element\\kktagent\\settings.json') as json_file:
            data = json.load(json_file)
    except:
        return False
    for key, val in data.items():
        if not isinstance(val, (list, dict)):
            setting_str_val = eval(f'settings.{key.upper()}')
            if setting_str_val != val:
                settings_modify(f'{key.upper()} = ', val)
    for key, val in data['kkt_parameters'].items():
        setting_str_val = eval(f'settings.{key.upper()}')
        if setting_str_val != val:
            settings_modify(f'{key.upper()} = ', val)
    for key, val in data['parameters'].items():
        setting_str_val = eval(f'settings.{key.upper()}')
        if setting_str_val != val:
            settings_modify(f'{key.upper()} = ', val)

    for model_kkt in data['models']:
        for key, val in model_kkt['parameters'].items():
            setting_str_val = eval(f'settings.{key.upper()}')
            if setting_str_val != val:
                settings_modify(f'{key.upper()} = ', val)
    login_pass = settings.LOGIN + settings.PASSWORD + settings.FN_NUMBER  # Сохраняем первый логин - пароль

    settings.reload()
    if login_pass != settings.LOGIN + settings.PASSWORD + settings.FN_NUMBER:
        return True
    else:
        return False



#from_setting_to_json()
#from_json_to_setting()
