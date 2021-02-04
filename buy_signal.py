import boto3
import config
import datetime
import pandas as pd
import pytz
from td.client import TDClient
import td_config
import td_helper2

df = td_helper2.get_signal_prices(5, td_helper2.get_symbols())

df_max = df[df['Date'].isin(pd.Series(df['Date'].unique()).nlargest(2))].reset_index(drop=True)

test = ['NIO']
results = []

for symbol in df_max['Symbol'].unique():
    df_one = df_max[df_max['Symbol'] == symbol]

    try:
        if ((df_one.iloc[-2]['Open'] < df_one.iloc[-2]['SMA_9']) and
                (df_one.iloc[-2]['Close'] < df_one.iloc[-2]['SMA_9']) and
                (df_one.iloc[-1]['Open'] < df_one.iloc[-1]['SMA_9']) and
                (df_one.iloc[-1]['Close'] > df_one.iloc[-1]['SMA_9'])):
            results.append([symbol, True])

        else:
            results.append([symbol, False])

    except:
        next

text_df = pd.DataFrame(results, columns=['Ticker', 'Text'])

client = boto3.client(
    "sns",
    aws_access_key_id = config.python_texter_ak,
    aws_secret_access_key = config.python_texter_sk,
    region_name = config.python_texter_region
)

text_df['Text'][4] = True

for i in range(0,len(text_df)):
    if text_df['Text'][i] == True:
        client.publish(PhoneNumber = config.python_texter_phone,
                       Message = "{} is now set up for a day trade on the 5-minute chart.".format(text_df['Ticker'][i]))
