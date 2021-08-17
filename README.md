# Trading Performance

This notebook retrieves your trade data from Binance to calculate the pnl from your trading.

The methodology for calculating PNL is:

1. Calculate the total amount of net base asset purchased (or sold) and the total amount of quote asset spent (or received)
2. Calculate the value of these changes based on current asset spot price
3. Calculate the value of the fees paid out in the trades

Note that this methodology is one way of trying to evaluate the benefit if your trading activity, i.e. doing something versus doing nothing. This does not capture any changes in portfolio value due to general market movements that may result in the appreciation of the value of base assets and quote assets.

## Requirements

-   Python 3.x

    > pip install -r requirements.txt

    > jupyter lab

## Usage

### Method 1 :

clone the repo, open the jupyter notebook, fill keys, run the notebook locally

### Method 2 :

Go to colab : https://colab.research.google.com/notebooks/intro.ipynb?utm_source=scs-index#recent=true  
open from github

### Method 3 :

Use a ready to go collab notebook(recommanded) :  
https://drive.google.com/file/d/1Z6Q0tX7Czj4w0FnliSiqmi-qUG9AfPeI/view?usp=sharing

## Instructions

Step 0) Select `Runtime` => `Run all`

Step 1) Input your **_read only_** API keys

Step 2) Input trading pair and start date

Step 3) click start

## Notes

-   `% gain and loss` is based on your current balance of base and quote asset. This may not be a comprehensive figure if (1) you have made deposits/withdrawals within the period being analyzed, and (2) if you are trading multiple pairs with overlapping base and quote assets

## Supported Exchanges:

-   binance ✅
-   kucoin ❌(07/15/21 changes).
-   ascendex ✅

## Comments / bugs / suggestions

Please email [carlo@hummingbot.io](mailto:carlol@hummingbot.io?subject=Colab:%20Performance%20Sheet).  
Please email [amine@hummingbot.io](mailto:amine@hummingbot.io?subject=Colab:%20Performance%20Sheet).
