from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
import pandas as pd
from kucoin.client import User as Client
from kucoin.client import Market
from kucoin.client import Trade
from datetime import datetime, timedelta


class KucoinClientWrapper(ExchangeClientWrapper):

    def __init__(self, kucoinClient, kucoinTrade, kucoinMarket):
        super().__init__(kucoinClient)
        self.marketClient = kucoinMarket
        self.tradeClient = kucoinTrade

    @staticmethod
    def createInstance(api_key, api_secret, api_passphrase=None):
        kucoinClient = Client(api_key, api_secret, api_passphrase)
        kucoinTrade = Trade(api_key, api_secret, api_passphrase)
        kucoinMarket = Market()
        return KucoinClientWrapper(kucoinClient, kucoinTrade, kucoinMarket)

    def usd_price_for(self, asset):
        stable_coins = ['USDT', 'USDC', 'BUSD', 'TUSD']
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                res = self.marketClient.get_ticker(symbol=f"{asset}-{c}")
                return float(res['price'])
            except:
                '"The symbol combination not supported"'
        print("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        """Give an asset return balance locked or free to use"""
        res = self.client.get_account_list(asset)
        asset_balance = 0
        for r in res:
            asset_balance += float(r['balance'])
        return asset_balance

    def symbol_info(self, trading_pair):
        # issue N 18 : https://github.com/Kucoin/kucoin-python-sdk/issues/18
        res = self.marketClient.get_symbol_list()
        for r in res:
            if r['symbol'] == trading_pair:
                trading_pair_info = r
                return trading_pair_info["baseCurrency"], trading_pair_info["quoteCurrency"]
        raise Exception("Trading pair is not valid for kucoin")

    def get_trades(self, symbol, start_timestamp):
        # I reproduce the same way dates are in kucoin API :(
        start_timestamp *= 1000
        df_trades = pd.DataFrame()
        currentPage = 1
        total_page = float('inf')
        while currentPage <= total_page:
            rs = self.tradeClient.get_fill_list(
                'TRADE', symbol=symbol, currentPage=currentPage, pageSize=500)
            currentPage += 1
            total_page = rs['totalPage']
            df_res = pd.DataFrame(rs['items'])
            if(len(df_res) == 0):
                break
            elif(len(df_trades) == 0):
                df_trades = df_res
            else:
                df_res = df_res[df_res['createdAt'] >= int(start_timestamp)]
                df_trades = df_trades.append(df_res, ignore_index=True)
        if len(df_trades) > 0:
            return self.format_data(df_trades)
        return pd.DataFrame()

    def format_data(self, df):
        df.rename(columns={'size': 'qty', 'funds': 'quoteQty',
                  'fee': 'commission', 'feeCurrency': 'commissionAsset'}, inplace=True)
        df['date_time'] = pd.to_datetime(df["createdAt"], unit="ms")
        fee_currencies = df['commissionAsset'].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f),
                   'commissionAssetUsdPrice'] = self.usd_price_for(f)
        df = df.astype({'price': 'float64', 'qty': 'float64', 'quoteQty': 'float64',
                       'commission': 'float64', 'commissionAssetUsdPrice': 'float64'})
        return df[['price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'side', 'commissionAssetUsdPrice', 'date_time']]
