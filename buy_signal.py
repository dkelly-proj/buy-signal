import boto3
import config
import datetime
import pandas as pd
import pytz
from td.client import TDClient
import td_config
import td_helper2

df = td_helper2.get_signal_prices(5, td_helper2.get_symbols())

td_helper2.send_sms_alert(df)