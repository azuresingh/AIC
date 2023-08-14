# from decouple import config

# SECRET_KEY = config('SECRET_KEY')
from decouple import config

# config_path = r'C:\Users\JoshiP02\Downloads\AIC_db_snow_ui_model_integrated_250723\AICMain250723readyfordemo\.env'
#config_path = r'.\.env'

SECRET_KEY = config('SECRET_KEY')

MYSQL_HOST = config('MYSQL_HOST')
MYSQL_USERNAME = config('MYSQL_USERNAME')
MYSQL_PASSWORD = config('MYSQL_PASSWORD')
MYSQL_DATABASE = config('MYSQL_DATABASE')

SERVICENOW_INSTANCE = config('SERVICENOW_INSTANCE')
SERVICENOW_USERNAME = config('SERVICENOW_USERNAME')
SERVICENOW_PASSWORD = config('SERVICENOW_PASSWORD')
pklfile = config('pklfile')
