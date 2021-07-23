from abc import ABC, abstractmethod
from requests import get
from requests.models import PreparedRequest
import json
import pandas as pd


class ExchangeClientWrapper(ABC):

    def __init__(self, client):
        self.client = client

    @staticmethod
    @abstractmethod
    def createInstance():
        pass

    @abstractmethod
    def usd_price_for(self, symbol):
        pass

    @abstractmethod
    def get_asset_balance(self, asset):
        pass

    def get_current_asset_balance(self, trading_pair):
        base_asset, quote_asset = self.symbol_info(trading_pair)
        df = pd.DataFrame(columns=["asset"], data=[
                          base_asset, quote_asset])
        df["price"] = df["asset"].apply(lambda x: self.usd_price_for(x))
        df["balance"] = df["asset"].apply(lambda x: self.get_asset_balance(x))
        df["usd_value"] = df["price"] * df["balance"]
        df.set_index("asset", inplace=True, drop=True)
        base_asset_price = df.at[base_asset, "price"]
        quote_asset_price = df.at[quote_asset, "price"]
        return df, base_asset, quote_asset, base_asset_price, quote_asset_price

    @abstractmethod
    def get_trades(self, symbol, start_date):
        pass

    @abstractmethod
    def format_data(self, df):
        pass

    @abstractmethod
    def symbol_info():
        raise NotImplementedError("exchange specifications")
