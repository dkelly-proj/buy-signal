import datetime
import pandas as pd
import pytz
import random
from td.client import TDClient
import td_config

# retrieve symbols from Radar watchlist
def get_symbols():
    TDSession = TDClient(
        client_id=td_config.client_id,
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
        client_id=td_config.client_id,
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