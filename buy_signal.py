# Standard imports
import boto3
import datetime
import pandas as pd
import pytz
from td.client import TDClient
import time

# Local imports
import config
import buy_signal_helper

# Set start time
starttime = time.time()

# Execute setup screen every two minutes
while True:
    df = buy_signal_helper.get_signal_prices(5, buy_signal_helper.get_symbols())
    buy_signal_helper.send_sms_alert(df)

    time.sleep(30.0 - ((time.time() - starttime) % 30.0))