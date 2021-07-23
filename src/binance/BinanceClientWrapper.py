from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
from binance.client import Client
import pandas as pd


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
                '"The symbol combination not supported"'
        print("we couldn't find price for this asset")

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

    def get_trades(self, symbol, start_dt):
        df_trades = pd.DataFrame()
        df = pd.DataFrame(self.client.get_my_trades(
            symbol=symbol, fromId=0, limit=1))
        if len(df) == 0:
            return df_trades
        first_id = int(df["id"].item())
        first_dt = pd.to_datetime(df["time"].item(), unit="ms")
        df_last = pd.DataFrame(
            self.client.get_my_trades(symbol=symbol, limit=1))
        last_id = int(df_last["id"].item())
        last_dt = pd.to_datetime(df_last["time"].item(), unit="ms")

        INTERVAL_COUNT = 10
        id_interval = int((last_id - first_id) / INTERVAL_COUNT)

        # find the first id from which to begin retrieving data
        while first_dt < start_dt:
            next_id = first_id + id_interval
            df = pd.DataFrame(self.client.get_my_trades(
                symbol=symbol, fromId=next_id, limit=1))
            if len(df) > 0:
                next_id = df["id"].item()
                next_dt = pd.to_datetime(df["time"].item(), unit="ms")
            else:
                next_dt = start_dt
            first_dt = next_dt

        # Retrieve trades
        max_id = first_id

        while max_id < last_id:
            df = pd.DataFrame(self.client.get_my_trades(
                symbol=symbol, fromId=max_id))
            if df_trades.empty:
                df_trades = df
            else:
                f_trades = pd.concat([df_trades, df])
            max_id = df["id"].max() + 1

        df_trades["date_time"] = pd.to_datetime(df_trades["time"], unit="ms")
        df_trades = df_trades[df_trades["date_time"] >= start_dt]
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
