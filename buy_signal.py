# Standard imports
import boto3
import datetime
import pandas as pd
import pytz
from td.client import TDClient
import time
import sys

# Local imports
import config
import buy_signal_helper

# Set start time
#starttime = time.time()

# Establish log for alerts
text_log = []

# Enter infinite loop
while True:

    # Loop until shutdown
    try:

        # Check that market is open
        if datetime.datetime.now().hour in [9,10,11,12,13,14,15,16]:
            
            # Get symbols from watchlist
            watchlist = buy_signal_helper.get_symbols('Radar')

            # Get price history for watchlist symbols
            df = buy_signal_helper.dt_signal_prices(5, watchlist)

            # Calculate signals
            df = buy_signal_helper.calculate_signal(df)

            # Send alerts
            text_log = buy_signal_helper.send_sms(df, text_log)

        else:
            print('Market currently closed - {}'.format(datetime.datetime.now()))

        # Execute every two minutes
        time.sleep(120)

    # When shutdown, print text log
    except KeyboardInterrupt:

        # Print log of alerts
        if len(text_log) < 1:
            print("No text alerts were sent.")

        else:
            print(pd.DataFrame(text_log, columns = ['Symbol','Date','Signal']))

        # Exit script
        print("Exiting...")
        sys.exit()