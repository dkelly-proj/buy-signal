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

# Establish log for alerts
text_log = []

# Execute setup screen every two minutes
while True:

    # Check that market is open
    if datetime.datetime.now() in [9,10,11,12,13,14,15,16]:
        
        # Get symbols from watchlist
        watchlist = buy_signal_helper.get_symbols('Radar')

        # Get price history for watchlist symbols
        df = buy_signal_helper.dt_signal_prices(5, watchlist)

        # Calculate signals
        df = buy_signal_helper.calculate_signal(df)

        # Send alerts
        buy_signal_helper.send_sms(df)

    time.sleep(120.0 - ((time.time() - starttime) % 120.0))