from src.abstract.ExchangeClientWrapper import ExchangeClientWrapper
from src.ascendex.AscendexRestApi import AscendexRestApi
import pandas as pd


class AscendexClientWrapper(ExchangeClientWrapper):

    @staticmethod
    def createInstance(api_key, api_secret, api_group):
        api_url = "https://ascendex.com/"
        client = AscendexRestApi(api_key, api_secret, api_group, api_url)
        return AscendexClientWrapper(client)

    def usd_price_for(self, asset):
        stable_coins = ['USDT', 'USDC', 'BUSD', 'TUSD']
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                res = self.client.getTicker(symbol=f"{asset}/{c}")
                return float(res['ask'][0])
            except Exception as e:
                print("The symbol combination not supported ")
        print("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        res = self.client.getBalance(asset=asset)
        if(len(res)):
            return float(res[0]['totalBalance'])
        return 0.0

    def get_all_asset_balances(self):
        res = self.client.getBalance()
        if(len(res)):
            return pd.DataFrame(res)
        return pd.DataFrame()
    
    def symbol_info(self, trading_pair):
        res = self.client.listAllProduct()
        for r in res:
            if r['symbol'] == trading_pair:
                trading_pair_info = r
                return trading_pair_info["baseAsset"], trading_pair_info["quoteAsset"]
        raise Exception("Trading pair is not valid for ascendex")

    def get_trades(self, symbol, start_date, account='cash'):
        data = self.client.getHistOrders(
            account=account, symbol=symbol, startTime=start_date)
        df_trades = pd.DataFrame(data)
        if(len(df_trades)):
            seqNum = df_trades.tail(1)['seqNum'].values[0]
            df_trades = df_trades[df_trades['status'] == 'Filled']
        else:
            raise Exception(
                f"We couldn't fetch trades for this trading pair {symbol}")

        while True:
            data = self.client.getHistOrders(
                account=account, symbol=symbol, startTime=start_date, seqNum=seqNum)
            df_res = pd.DataFrame(data)
            lastRetrievedseqNum = df_res.tail(1)['seqNum'].values[0]
            if(lastRetrievedseqNum == seqNum):
                break
            else:
                seqNum = df_res.tail(1)['seqNum'].values[0]
                df_res = df_res[df_res['status'] == 'Filled']
                df_trades = df_trades.append(df_res, ignore_index=True)
        return self.format_data(df_trades)

    def format_data(self, df):
        df.loc[(df["side"] == 'Sell'), 'side'] = 'sell'
        df.loc[(df["side"] == 'Buy'), 'side'] = 'buy'

        df.rename(columns={
            "createTime": "date_time",
            "orderQty": "qty",
            "fee": "commission",
            "feeAsset": "commissionAsset",
        }, inplace=True)
        df['date_time'] = pd.to_datetime(df["date_time"], unit="ms")
        fee_currencies = df['commissionAsset'].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f),
                   'commissionAssetUsdPrice'] = self.usd_price_for(f)
        df = df.astype({'price': 'float64', 'qty': 'float64',
                       'commission': 'float64', 'commissionAssetUsdPrice': 'float64'})
        df['quoteQty'] = (df.price*df.qty).astype('float64')
        return df[['price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'side', 'commissionAssetUsdPrice', 'date_time']]
