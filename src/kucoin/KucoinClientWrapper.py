from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
import pandas as pd      
from kucoin.client import User as Client
from kucoin.client import Market
from kucoin.client import Trade
from datetime import datetime,timedelta


class KucoinClientWrapper(ExchangeClientWrapper):

    def __init__(self,kucoinClient,kucoinTrade,kucoinMarket):
        super().__init__(kucoinClient)
        self.marketClient = kucoinMarket
        self.tradeClient = kucoinTrade

    @staticmethod
    def createInstance(api_key, api_secret,api_passphrase =None):
        kucoinClient = Client(api_key, api_secret,api_passphrase)
        kucoinTrade = Trade(api_key, api_secret,api_passphrase)
        kucoinMarket = Market()
        
        return KucoinClientWrapper(kucoinClient,kucoinTrade,kucoinMarket)

    def usd_price_for(self,asset):
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
            asset_balance +=float(r['balance'])
        return asset_balance

    def get_current_asset_balance(self, trading_pair):
        #issue N 18 : https://github.com/Kucoin/kucoin-python-sdk/issues/18 
        res = self.marketClient.get_symbol_list()
        for r in res:
            if r['symbol'] == trading_pair:
                trading_pair_info = r
        base_asset = trading_pair_info["baseCurrency"]
        quote_asset = trading_pair_info["quoteCurrency"]
        df = pd.DataFrame(columns=["asset"], data=[
                          base_asset, quote_asset])
        df["price"] = df["asset"].apply(lambda x: self.usd_price_for(x))
        df["balance"] = df["asset"].apply(lambda x: self.get_asset_balance(x))
        df["usd_value"] = df["price"] * df["balance"]
        df.set_index("asset", inplace=True, drop=True)
        base_asset_price = df.at[base_asset, "price"]
        quote_asset_price = df.at[quote_asset, "price"]
        return df,base_asset,quote_asset,base_asset_price,quote_asset_price
    
    def get_trades(self,symbol,start_dt=datetime.today()):
        df_trades = pd.DataFrame()
        while True:
            currentPage = 1
            total_page = float('inf')
            while currentPage < total_page:
                rs = self.tradeClient.get_fill_list('TRADE',symbol=symbol,currentPage=currentPage,pageSize=500)
                if(len(df_trades)==0):
                    df_trades = pd.DataFrame(rs['items'])
                else:
                    return self.format_data(df_trades)
                    df_trades = pd.concat(df_trades, pd.DataFrame(rs['items']))
                currentPage +=1
                total_page = rs['totalPage']
            start_dt = start_dt + timedelta(days=7)
        return self.format_data(df_trades)

    def get_trades(self,symbol,start_timestamp):
        start_timestamp *=1000 #I reproduce the same way dates are in kucoin API :(
        df_trades = pd.DataFrame()
        currentPage = 1
        total_page = float('inf')
        while currentPage <= total_page:
            rs = self.tradeClient.get_fill_list('TRADE',symbol=symbol,currentPage=currentPage,pageSize=500)
            currentPage +=1
            total_page = rs['totalPage']
            df_res = pd.DataFrame(rs['items'])
            df_res = df_res[df_res['createdAt'] >= int(start_timestamp)]
            if(len(df_res)==0):
                break
            elif(len(df_trades)==0):
                df_trades = df_res
            else: 
                df_trades =  df_trades.append(df_res,ignore_index=True)
        return self.format_data(df_trades)

    def format_data(self,df):
        df.rename(columns={'size':'qty','funds':'quoteQty','fee':'commission','feeCurrency':'commissionAsset'},inplace=True)
        df['date_time'] = pd.to_datetime(df["createdAt"], unit="ms")
        fee_currencies = df['commissionAsset'].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f),'commissionAssetUsdPrice'] = self.usd_price_for(f)
        df = df.astype({'price':'float64','qty':'float64','quoteQty':'float64','commission':'float64','commissionAssetUsdPrice':'float64'})
        return df[['price','qty','quoteQty','commission','commissionAsset','side','commissionAssetUsdPrice','date_time']]