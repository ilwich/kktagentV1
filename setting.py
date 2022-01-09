from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",  # export envvars with `export DYNACONF_FOO=bar`.
    settings_files=['settings.toml', '.secrets.toml'],  # Load files in the given order.
)

