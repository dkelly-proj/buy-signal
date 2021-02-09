# Standard imports
import boto3
import datetime
import pandas as pd
import pytz
from td.client import TDClient

# Local imports
import config

# retrieve symbols from Radar watchlist
def get_symbols(watchlist):
    TDSession = TDClient(
        client_id=config.client_id,
        redirect_uri='http://localhost/test',
        credentials_path='td_state.json')

    TDSession.login()

    response = TDSession.get_watchlist_accounts()

    i = 0

    for r in response:
        if r['name'] == str(watchlist):
            watch = response[i]
            symbols = [watch['watchlistItems'][x]['instrument']['symbol'] for x in range(len(watch['watchlistItems']))]
        else:
            i += 1
            
    return symbols

# Get prices for Radar charts
def dt_signal_prices(candle_minutes, symbols):
    TDSession = TDClient(
        client_id=config.client_id,
        redirect_uri='http://localhost/test',
        credentials_path='td_state.json')

    TDSession.login()

    cur_day = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    price_end_date = str(int(round(cur_day.timestamp() * 1000)))
    price_start_date = str(int(round(datetime.datetime(cur_day.year, cur_day.month, cur_day.day-1).timestamp() * 1000)))

    candle_list = []

    for symbol in symbols:
        p_hist = TDSession.get_price_history(symbol,
                                             period_type='day',
                                             frequency_type='minute',
                                             frequency=str(candle_minutes),
                                             end_date=price_end_date,
                                             start_date=price_start_date)

        for candle in p_hist['candles']:
            candle_list.append([symbol,
                                datetime.datetime.fromtimestamp(candle['datetime'] / 1000),
                                candle['open'],
                                candle['close'],
                                candle['high'],
                                candle['low']])

    df_dt = pd.DataFrame(candle_list, columns = ['Symbol', 'Date', 'Open', 'Close', 'High', 'Low'])

    # Calculate moving average
    df_dt['SMA_9'] = df_dt.groupby('Symbol')['Close'].rolling(9).mean().reset_index(0,drop=True)

    return df_dt

def calculate_signal(dataframe):
    df = dataframe
    df_max = df[df['Date'].isin(pd.Series(df['Date'].unique()).nlargest(3))].reset_index(drop=True)

    signal = []

    for symbol in df_max['Symbol'].unique():
        df_test = df_max[df_max['Symbol'] == symbol].reset_index(drop = True)
        
        if len(df_test) == 3:
            try:
                for i in range(2, len(df_test)):
                    low_candle = (df_test.iloc[-3]['Open'] < df_test.iloc[-3]['SMA_9'] and
                                  df_test.iloc[-3]['Close'] < df_test.iloc[-3]['SMA_9'])

                    breakout_candle = (df_test.iloc[-2]['Open'] < df_test.iloc[-2]['SMA_9'] and
                                       df_test.iloc[-2]['Close'] > df_test.iloc[-2]['SMA_9'] and
                                       # Breakout greater than 1%
                                       (df_test.iloc[-2]['Close'] - df_test.iloc[-2]['Open'])/df_test.iloc[-2]['Open']*100 > 1)

                    confirmation_candle = (df_test.iloc[-1]['Open'] > df_test.iloc[-1]['SMA_9'] and
                                           df_test.iloc[-1]['Close'] > df_test.iloc[-1]['SMA_9'] and
                                           df_test.iloc[-1]['Close'] > df_test.iloc[-1]['Open'])

                    signal.append([symbol,
                                   df_test.iloc[-1]['Date'],
                                   low_candle == True and breakout_candle == True and confirmation_candle == True])
       
            except:
                next              

    return pd.DataFrame(signal, columns = ['Symbol','Date','Signal'])

def send_sms(dataframe, text_log):
    df = dataframe
    
    client = boto3.client("sns",
                          aws_access_key_id = config.python_texter_ak,
                          aws_secret_access_key = config.python_texter_sk,
                          region_name = config.python_texter_region)
    
    for i in range(0,len(df)):
        if df['Signal'][i] == True:
            
            duplicate = ([df['Symbol'][i], df['Date'][i], df['Signal'][i]] in text_log)
            
            if not duplicate:
                client.publish(PhoneNumber = config.python_texter_phone,
                               Message = "{} is now set up for a day trade on the 5-minute chart.".format(df['Symbol'][i]))
                
                text_log.append([df['Symbol'][i], df['Date'][i], df['Signal'][i]])
                
    print("Process completed, {} text alerts have been sent - {}".format(len(text_log), datetime.datetime.now()))
    return text_log