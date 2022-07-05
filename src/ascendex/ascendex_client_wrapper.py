import time

import pandas as pd

from src.abstract.exchange_client_wrapper import ExchangeClientWrapper
from src.ascendex.ascendex_rest_api import AscendexRestApi


class AscendexClientWrapper(ExchangeClientWrapper):
    @staticmethod
    def create_instance(api_key, api_secret, api_group):
        api_url = "https://ascendex.com/"
        client = AscendexRestApi(key=api_key, secret=api_secret, group=api_group, url=api_url)
        return AscendexClientWrapper(client)

    def usd_price_for(self, asset):
        stable_coins = ["USDT", "USDC", "BUSD", "TUSD"]
        if asset in stable_coins:
            return 1
        for c in stable_coins:
            try:
                res = self.client.get_ticker(symbol=f"{asset}/{c}")
                return float(res["ask"][0])
            except Exception:
                print("The symbol combination not supported ")
        print("we couldn't find price for this asset")

    def get_asset_balance(self, asset):
        res = self.client.get_balance(asset=asset)
        if len(res):
            return float(res[0]["totalBalance"])
        return 0.0

    def get_all_asset_balances(self):
        res = self.client.get_balance()
        if len(res):
            df = pd.DataFrame(res)
            for field in ["totalBalance", "availableBalance"]:
                df[field] = df[field].apply(float)
            return df
        return pd.DataFrame()

    def symbol_info(self, trading_pair):
        res = self.client.list_all_product()
        for r in res:
            if r["symbol"] == trading_pair:
                trading_pair_info = r
                return trading_pair_info["baseAsset"], trading_pair_info["quoteAsset"]
        raise Exception("Trading pair is not valid for ascendex")

    def get_trades(self, symbol, start_date, end_date=round(time.time() * 1000), account="cash"):
        """
        fetching all orders history filled and opened ones.

        to optimize : fetch only filled (not available in api .v2)
        """
        df_trades = pd.DataFrame()
        seq_num = -1
        while start_date <= end_date:
            rs = None
            try:
                if seq_num == -1:
                    rs = self.client.getHistOrders(
                        account=account,
                        symbol=symbol,
                        startTime=start_date,
                        endTime=end_date,
                    )
                else:
                    rs = self.client.get_hist_order(
                        account=account,
                        symbol=symbol,
                        startTime=start_date,
                        endTime=end_date,
                        seqNum=seq_num,
                    )
            except Exception as e:
                code, msg = e.args
                if code == 429:
                    print("exceed limit rate sleep for 1min 💤")
                    time.sleep(61)
                    continue
                else:
                    raise Exception(e.args)
            df_res = pd.DataFrame(rs)
            if len(df_res) == 0:
                break
            elif len(df_trades) == 0:
                seq_num = df_res.iloc[-1]["seqNum"] + 1
                df_trades = df_res[df_res["fillQty"] != "0"]
            else:
                seq_num = df_res.iloc[-1]["seqNum"] + 1
                df_res = df_res[df_res["fillQty"] != "0"]
                df_trades = df_res.append(df_trades, ignore_index=True)
        if len(df_trades) > 0:
            df_trades.reset_index(drop=True, inplace=True)
            df_trades.sort_values("lastExecTime", ascending=False, ignore_index=True, inplace=True)
            return self.format_data(df_trades)
        raise Exception(f"We couldn't fetch trades for this trading pair {symbol}")

    def format_data(self, df):
        df.loc[(df["side"] == "Sell"), "side"] = "sell"
        df.loc[(df["side"] == "Buy"), "side"] = "buy"

        df.rename(
            columns={
                "lastExecTime": "date_time",
                "orderQty": "qty",
                "fee": "commission",
                "feeAsset": "commissionAsset",
            },
            inplace=True,
        )
        df["date_time"] = pd.to_datetime(df["date_time"], unit="ms")
        fee_currencies = df["commissionAsset"].unique()
        for f in fee_currencies:
            df.loc[(df["commissionAsset"] == f), "commissionAssetUsdPrice"] = self.usd_price_for(f)
        df = df.astype(
            {
                "price": "float64",
                "qty": "float64",
                "commission": "float64",
                "commissionAssetUsdPrice": "float64",
            }
        )
        df["quoteQty"] = (df.price * df.qty).astype("float64")
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
