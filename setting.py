from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",  # export envvars with `export DYNACONF_FOO=bar`.
    settings_files=['C:\\ProgramData\\V_element\\kktagent\\settings.toml',
                    'C:\\ProgramData\\V_element\\kktagent\\.secrets.toml'],  # Load files in the given order.
)

