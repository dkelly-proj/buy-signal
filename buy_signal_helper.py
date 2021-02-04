# Standard imports
import boto3
import datetime
import pandas as pd
import pytz
from td.client import TDClient

# Local imports
import config

# retrieve symbols from Radar watchlist
def get_symbols():
    TDSession = TDClient(
        client_id=config.client_id,
        redirect_uri='http://localhost/test',
        credentials_path='td_state.json')

    TDSession.login()

    response = TDSession.get_watchlist_accounts()

    i = 0

    for r in response:
        if r['name'] == 'Radar':
            watch = response[i]
            symbols = [watch['watchlistItems'][x]['instrument']['symbol'] for x in range(len(watch['watchlistItems']))]
        else:
            i += 1
            
    return symbols

# Get prices for Radar charts
def get_signal_prices(candle_minutes, symbols):
    TDSession = TDClient(
        client_id=config.client_id,
        redirect_uri='http://localhost/test',
        credentials_path='td_state.json')

    TDSession.login()

    cur_day = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    price_end_date = str(int(round(cur_day.timestamp() * 1000)))
    price_start_date = str(int(round(datetime.datetime(cur_day.year, cur_day.month, cur_day.day-1).timestamp() * 1000)))

    sym = []
    da = []
    op = []
    cl = []
    hi = []
    lo = []

    for symbol in symbols:
        p_hist = TDSession.get_price_history(symbol,
                                             period_type='day',
                                             frequency_type='minute',
                                             frequency=str(candle_minutes),
                                             end_date=price_end_date,
                                             start_date=price_start_date)

        for candle in p_hist['candles']:
            sym.append(symbol)
            da.append(datetime.datetime.fromtimestamp(candle['datetime'] / 1000))
            op.append(candle['open'])
            cl.append(candle['close'])
            hi.append(candle['high'])
            lo.append(candle['low'])

    df_p_hist = pd.DataFrame({'Symbol': sym, 'Date': da, 'Open': op,
                              'Close': cl, 'High': hi, 'Low': lo})

    # Calculate moving average
    df_p_hist['SMA_9'] = df_p_hist.groupby('Symbol')['Close'].rolling(9).mean().reset_index(0,drop=True)

    return df_p_hist

def send_sms_alert(dataframe):
    df = dataframe
    df_max = df[df['Date'].isin(pd.Series(df['Date'].unique()).nlargest(2))].reset_index(drop=True)

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

    for i in range(0,len(text_df)):
        if text_df['Text'][i] == True:
            client.publish(PhoneNumber = config.python_texter_phone,
                           Message = "{} is now set up for a day trade on the 5-minute chart.".format(text_df['Ticker'][i]))

    print("Process completed - {}".format(datetime.datetime.now()))