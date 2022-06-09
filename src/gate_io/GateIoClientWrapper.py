from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
from gate_api import ApiClient, SpotApi, Configuration
import pandas as pd
from gate_api.exceptions import GateApiException, ApiException
import time
import requests
import json

class GateIoClientWrapper(ExchangeClientWrapper):

    def __init__(self, gateIoClient, gateIoSpot):
        super().__init__(gateIoClient)
        self.spotClient = gateIoSpot


    @staticmethod
    def createInstance(api_key, api_secret):
        configuration = Configuration(
            key = api_key,
            secret = api_secret
        )
        gateIoClient = ApiClient(configuration)
        gateIoSpot = SpotApi(gateIoClient)
        return GateIoClientWrapper(gateIoClient, gateIoSpot)


    def usd_price_for(self, asset):
        stable_coins = ['USDT', 'USDC', 'BUSD', 'TUSD']
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                # Retrieve ticker information
                api_response = self.spotClient.list_tickers(currency_pair=f"{asset}_{c}")
                return float(api_response[0].lowest_ask)
            except GateApiException as ex:
                print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
            except ApiException as e:
                print("Exception when calling SpotApi->list_tickers: %s\n" % e)
            except Exception as e:
                print("The symbol combination not supported ")
        print("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        try:
            # List spot accounts
            api_response = self.spotClient.list_spot_accounts(currency=f"{asset}")
            asset_balance = float(api_response[0].available) + float(api_response[0].locked)
            return asset_balance
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_spot_accounts: %s\n" % e)

    def symbol_info(self, trading_pair):
        try:
            # List all currency pairs supported
            api_response = self.spotClient.list_currency_pairs()
            for r in api_response:
                if r.id == trading_pair:
                    return r.base, r.quote
            raise Exception("Trading pair is not valid for gateio")
        except GateApiException as ex:
            print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
        except ApiException as e:
            print("Exception when calling SpotApi->list_currency_pairs: %s\n" % e)


    def get_trades(self, symbol, start_date,end_date=round(time.time() * 1000)):
        df_trades = pd.DataFrame()
        start_date = round(start_date/1000)
        end_date = round(end_date/1000)
        while start_date<=end_date:
            try:
                trades = self.spotClient.list_my_trades(
                    symbol, limit=500, _from=start_date, to=end_date)

                trades = [ trade.to_dict() for trade in trades ]
                for trade in trades:
                    trade['create_time'] = int(trade['create_time'])
                    trade['create_time_ms'] = round(float(trade['create_time_ms']))
                
                df_res = pd.DataFrame( trades )

                if(len(df_res) == 0):
                    break
                elif(len(df_trades) == 0):
                    start_date = int(df_res.iloc[0]['create_time'])+1
                    df_trades = df_res[df_res['create_time'] <= end_date]
                else:
                    start_date = int(df_res.iloc[0]['create_time'])+1
                    df_res = df_res[df_res['create_time'] <= end_date]
                    df_trades = df_res.append(df_trades, ignore_index=True)

            except GateApiException as ex:
                print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
            except ApiException as e:
                print("Exception when calling SpotApi->list_my_trades: %s\n" % e)

        if len(df_trades) == 0:
            raise Exception(
                f"We couldn't fetch trades for this trading pair {symbol}")

        df_trades["date_time"] = pd.to_datetime(df_trades["create_time_ms"], unit="ms")
        df_trades.set_index("id", inplace=True, drop=True)
        float_columns = ["price", "amount", "fee"]
        df_trades[float_columns] = df_trades[float_columns].apply(
            pd.to_numeric)
        return self.format_data(df_trades)

    def format_data(self, df):
        df.rename(columns={
            "amount": "qty",
            "fee": "commission",
            "fee_currency": "commissionAsset",
        }, inplace=True)
        fee_currencies = df['commissionAsset'].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f),
                   'commissionAssetUsdPrice'] = self.usd_price_for(f)
        df = df.astype({'price': 'float64', 'qty': 'float64',
                       'commission': 'float64', 'commissionAssetUsdPrice': 'float64'})
        df['quoteQty'] = (df.price*df.qty).astype('float64')
        return df[['price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'side', 'commissionAssetUsdPrice', 'date_time']]
