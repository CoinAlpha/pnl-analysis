from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
from binance.client import Client
import pandas as pd
from binance.exceptions import BinanceAPIException
import time
import requests
import json

class BinanceClientWrapper(ExchangeClientWrapper):

    @staticmethod
    def createInstance(api_key, api_secret):
        binanceClient = Client(api_key, api_secret)
        return BinanceClientWrapper(binanceClient)

    def usd_price_for(self, asset):
        stable_coins = ['USDT', 'USDC', 'BUSD', 'TUSD']
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                res = self.client.get_ticker(symbol=f"{asset}{c}")
                return float(res['lastPrice'])
            except:
                # edge cases like PIVX, there is no PIVXUSDT pair on binance
                endpoint = f"https://min-api.cryptocompare.com/data/price?fsym={asset}&tsyms=USD"
                res = requests.get(endpoint)
                res_json = json.loads(res.text)
                return(res_json["USD"])

        raise Exception("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        """Give an asset return balance locked or free to use"""
        balances = self.client.get_asset_balance(asset)
        asset_balance = float(balances["free"]) + float(balances["locked"])
        return asset_balance

    def symbol_info(self, trading_pair):
        trading_pair_info = self.client.get_symbol_info(trading_pair)
        if(trading_pair_info):
            base_asset = trading_pair_info["baseAsset"]
            quote_asset = trading_pair_info["quoteAsset"]
            return base_asset, quote_asset
        raise Exception("Trading pair is not valid for binance")

    def get_trades(self, symbol, start_date,end_date=round(time.time() * 1000)):
        df_trades = pd.DataFrame()
        while start_date<=end_date:
            try:
                df_res = pd.DataFrame(self.client.get_my_trades(
                        symbol=symbol, startTime=start_date))
                if(len(df_res) == 0):
                    break
                elif(len(df_trades)==0):
                    start_date = df_res.iloc[-1]['time']+1
                    df_trades = df_res[df_res['time'] <= end_date].sort_values(
                    'time', ascending=False, ignore_index=True)
                else:
                    start_date = df_res.iloc[-1]['time']+1
                    df_res = df_res[df_res['time'] <= end_date].sort_values(
                    'time', ascending=False, ignore_index=True)
                    df_trades = pd.concat([df_res,df_trades])
            except BinanceAPIException as err:
                if err.code == -1003:
                    print("exceed limit rate sleep for 1min 💤")
                    time.sleep(61)

        if len(df_trades) == 0:
            raise Exception(
                f"We couldn't fetch trades for this trading pair {symbol}")
        df_trades["date_time"] = pd.to_datetime(df_trades["time"], unit="ms")
        df_trades.set_index("id", inplace=True, drop=True)
        float_columns = ["price", "qty", "quoteQty", "commission"]
        df_trades[float_columns] = df_trades[float_columns].apply(
            pd.to_numeric)
        return self.format_data(df_trades)

    def format_data(self, df):
        df.loc[(df["isBuyer"] == False), 'side'] = 'sell'
        df.loc[(df["isBuyer"] == True), 'side'] = 'buy'
        fee_currencies = df['commissionAsset'].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f),
                   'commissionAssetUsdPrice'] = self.usd_price_for(f)
        df = df.astype({'price': 'float64', 'qty': 'float64', 'quoteQty': 'float64',
                       'commission': 'float64', 'commissionAssetUsdPrice': 'float64'})
        return df[['price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'side', 'commissionAssetUsdPrice', 'date_time']]
