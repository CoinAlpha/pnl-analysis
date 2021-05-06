from abc import ABC, abstractmethod
from requests import get
from requests.models import PreparedRequest
import json


class ExchangeClientWrapper(ABC):

    def __init__(self, client):
        self.client = client

    @staticmethod
    @abstractmethod
    def createInstance():
        pass
    
    @abstractmethod
    def usd_price_for(self,symbol):
        pass
    
    @abstractmethod
    def get_asset_balance(self, asset):
        pass

    @abstractmethod
    def get_current_asset_balance(self, trading_pair):
        pass

    @abstractmethod
    def get_trades(self, symbol, start_date):
        pass

    @abstractmethod
    def format_data(self,df):
        pass