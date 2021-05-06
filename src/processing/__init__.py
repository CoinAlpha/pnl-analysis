
import pandas as pd

def pnl_calculate(df,current_balance,meta):
    total_balance_usd = current_balance['usd_value'].sum()
    base_asset=meta['base_asset']
    quote_asset=meta['quote_asset']
    base_asset_price=meta['base_asset_price']
    quote_asset_price=meta['quote_asset_price']
    df_buys = df[df["side"] == "buy"]
    df_sells = df[df["side"] == "sell"]
    
    num_trades = len(df)
    num_buys = len(df_buys)
    num_sells = len(df_sells)
    
    columns = ["Label", f"Base ({base_asset})", f"Quote ({quote_asset})", "Total"]

    base_buys = df_buys["qty"].sum()
    base_sells = df_sells["qty"].sum()    
    quote_proceeds = df_sells["quoteQty"].sum()
    quote_spent = df_buys["quoteQty"].sum()

    base_delta = base_buys - base_sells
    quote_delta = quote_proceeds - quote_spent

    base_delta_usd = base_delta * base_asset_price
    quote_delta_usd = quote_delta * quote_asset_price

    trade_pnl = base_delta_usd + quote_delta_usd
    
    # Calculate trading fees
    total_fees_usd, df_commissions = calc_trading_fees(df)
    
    net_pnl = trade_pnl - total_fees_usd

    data = [
    ["Acquired", base_buys, quote_proceeds, "-"],
    ["Disposed", base_sells, quote_spent, "-"],
    ["Delta", base_delta, quote_delta, "-"],
    ["Delta (usd)", base_delta_usd, quote_delta_usd, base_delta_usd + quote_delta_usd],
    ["Trading fees (usd value)", "-", "-", -total_fees_usd],
    ["Net pnl (USD)", "-", "-", net_pnl],
    ["% gain/loss", "-", "-", f"{net_pnl / (total_balance_usd - net_pnl):.1%}"]
    ]

    df_summary_table = pd.DataFrame(columns=columns, data=data)
    df_summary_table.set_index("Label", inplace=True, drop=True)
    
    summary = {
        "first trade": df["date_time"].min().replace(microsecond=0),
        "last trade":df["date_time"].max().replace(microsecond=0),
        "total trades":num_trades,
        "- buys":f"{num_buys} / {num_buys/num_trades:.1%}",
        "- sells":f"{num_sells} / {num_sells/num_trades:.1%}",
        "total base traded":f"{df['qty'].sum():,.0f}",
        "total quote traded":f"{df['quoteQty'].sum():,.0f}",
        "approx. usd volume":f"${df['qty'].sum() * base_asset_price:,.0f}"
    }
    
    return summary,df_summary_table,total_fees_usd,df_commissions
    

def calc_trading_fees(df):
    total_fees_usd = 0

    df_commissions = df.groupby(["commissionAsset"]).agg({"commission": sum,'commissionAssetUsdPrice': 'first'})

    for asset in df_commissions.index:
        amount = df_commissions.loc[asset]["commission"]
        price = df_commissions.loc[asset]['commissionAssetUsdPrice']
        fees_usd = amount * price
        total_fees_usd += fees_usd

    return total_fees_usd, df_commissions