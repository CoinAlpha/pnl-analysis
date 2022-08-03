import time

import pandas as pd

from kucoin.client import Market, Trade
from kucoin.client import User as Client
from src.abstract.exchange_client_wrapper import ExchangeClientWrapper


class KucoinClientWrapper(ExchangeClientWrapper):
    def __init__(self, kucoin_client, kucoin_trade, kucoin_market):
        super().__init__(kucoin_client)
        self.marketClient = kucoin_market
        self.tradeClient = kucoin_trade

    @staticmethod
    def create_instance(api_key, api_secret, api_passphrase=None):
        kucoin_client = Client(key=api_key, secret=api_secret, passphrase=api_passphrase)
        kucoin_trade = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase)
        kucoin_market = Market()
        return KucoinClientWrapper(kucoin_client=kucoin_client, kucoin_trade=kucoin_trade, kucoin_market=kucoin_market)

    def usd_price_for(self, asset):
        stable_coins = ["USDT", "USDC", "BUSD", "TUSD"]
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                res = self.marketClient.get_ticker(symbol=f"{asset}-{c}")
                return float(res["price"])
            except Exception:
                """The symbol combination not supported."""
        print("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        """Give an asset return balance locked or free to use."""
        res = self.client.get_account_list(asset)
        asset_balance = 0
        if "data" in res:
            return asset_balance
        for r in res:
            asset_balance += float(r["balance"])
        return asset_balance

    def symbol_info(self, trading_pair):
        # issue N 18 : https://github.com/Kucoin/kucoin-python-sdk/issues/18
        res = self.marketClient.get_symbol_list()
        for r in res:
            if r["symbol"] == trading_pair:
                trading_pair_info = r
                return (
                    trading_pair_info["baseCurrency"],
                    trading_pair_info["quoteCurrency"],
                )
        raise Exception("Trading pair is not valid for kucoin")

    def get_trades(self, symbol, start_date, end_date=round(time.time() * 1000)):
        df_trades = pd.DataFrame()
        while start_date <= end_date:
            rs = self.tradeClient.get_fill_list("TRADE", symbol=symbol, pageSize=500, startAt=start_date)
            df_res = pd.DataFrame(rs["items"])
            if len(df_res) == 0:
                break
            elif len(df_trades) == 0:
                start_date = df_res.iloc[0]["createdAt"] + 1
                df_trades = df_res[df_res["createdAt"] <= end_date]
            else:
                start_date = df_res.iloc[0]["createdAt"] + 1
                df_res = df_res[df_res["createdAt"] <= end_date]
                df_trades = df_res.append(df_trades, ignore_index=True)
        if len(df_trades) > 0:
            df_trades.reset_index(drop=True, inplace=True)
            return self.format_data(df_trades)
        raise Exception(f"We couldn't fetch trades for this trading pair {symbol}")

    def format_data(self, df):
        df.rename(
            columns={
                "size": "qty",
                "funds": "quoteQty",
                "fee": "commission",
                "feeCurrency": "commissionAsset",
            },
            inplace=True,
        )
        df["date_time"] = pd.to_datetime(df["createdAt"], unit="ms")
        fee_currencies = df["commissionAsset"].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f), "commissionAssetUsdPrice"] = self.usd_price_for(f)
        df = df.astype(
            {
                "price": "float64",
                "qty": "float64",
                "quoteQty": "float64",
                "commission": "float64",
                "commissionAssetUsdPrice": "float64",
            }
        )
        return df[
            [
                "price",
                "qty",
                "quoteQty",
                "commission",
                "commissionAsset",
                "side",
                "commissionAssetUsdPrice",
                "date_time",
            ]
        ]
