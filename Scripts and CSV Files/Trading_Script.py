import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import numpy as np 

# === Process one AI's portfolio ===
def process_portfolio(portfolio, starting_cash):
    results = []
    total_value = 0
    total_pnl = 0
    cash = starting_cash
    tickers_to_remove = []
    for _, stock in portfolio.iterrows():
        ticker = stock["ticker"]
        shares = int(stock["shares"])
        cost = stock["buy_price"]
        stop = stock["stop_loss"]
        data = yf.Ticker(ticker).history(period="1d")

        if data.empty:
            print(f"[ChatGPT] No data for {ticker}")
            row = {
                "Date": today,
                "Ticker": ticker,
                "Shares": shares,
                "Cost Basis": cost,
                "Stop Loss": stop,
                "Current Price": "",
                "Total Value": "",
                "PnL": "",
                "Action": "NO DATA",
                "Cash Balance": "",
                "Total Equity": ""
            }
        else:
            price = round(data["Close"].iloc[-1], 2)
            value = round(price * shares, 2)
            pnl = round((price - cost) * shares, 2)

            if price <= stop:
                action = "SELL - Stop Loss Triggered"
                cash += value
                log_sell( ticker, shares, price, cost, pnl, action)
                tickers_to_remove.append(ticker)
            else:
                action = "HOLD"
                total_value += value
                total_pnl += pnl

            row = {
                "Date": today,
                "Ticker": ticker,
                "Shares": shares,
                "Cost Basis": cost,
                "Stop Loss": stop,
                "Current Price": price,
                "Total Value": value,
                "PnL": pnl,
                "Action": action,
                "Cash Balance": "",
                "Total Equity": ""
            }

        results.append(row)

    # === Add TOTAL row ===
    total_row = {
        "Date": today,
        "Ticker": "TOTAL",
        "Shares": "",
        "Cost Basis": "",
        "Stop Loss": "",
        "Current Price": "",
        "Total Value": round(total_value, 2),
        "PnL": round(total_pnl, 2),
        "Action": "",
        "Cash Balance": round(cash, 2),
        "Total Equity": round(total_value + cash, 2)
    }
    results.append(total_row)

    # === Save to CSV ===
    file = f"Scripts and CSV Files/chatgpt_portfolio_update.csv"
    df = pd.DataFrame(results)

    if os.path.exists(file):
        existing = pd.read_csv(file)
        existing = existing[existing["Date"] != today]  # Remove today's rows
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(file, index=False)

    # Remove sold stocks from the portfolio
    portfolio = portfolio[~portfolio['ticker'].isin(tickers_to_remove)]

    return portfolio, cash

# === Trade Logger (purely for stoplosses)===
def log_sell( ticker, shares, price, cost, pnl, reason="AUTOMATED SELL - STOPLOSS TRIGGERED"):
    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Sold": shares,
        "Sell Price": price,
        "Cost Basis": cost,
        "PnL": pnl,
        "Reason": reason
    }

    file = f"Scripts and CSV Files/chatgpt_trade_log.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(file, index=False)

# === Manual Buy Logger ===

def log_manual_buy(buy_price, shares, ticker, cash, stoploss, chatgpt_portfolio):
    check = input(f"""You are currently trying to buy {ticker}.
                   If this a mistake enter 1.""")
    if check == "1":
        raise SystemExit("Please remove this function call.")

    data = yf.download(ticker, period="1d")
    if data.empty:
        SystemExit(f"error, could not find ticker {ticker}")
    if buy_price * shares > cash:
        SystemExit(f"error, you have {cash} but are trying to spend {buy_price * shares}. Are you sure you can do this?")
    pnl = 0.0

    log = {
            "Date": today,
            "Ticker": ticker,
            "Shares Bought": shares,
            "Buy Price": buy_price,
            "Cost Basis": buy_price * shares,
            "PnL": pnl,
            "Reason": "MANUAL BUY - New position"
            }

    file = "Scripts and CSV Files/chatgpt_trade_log.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(file, index=False)
    new_trade = {"ticker": ticker, "shares": shares, "stop_loss": stoploss,
                "buy_price": buy_price, "cost_basis": buy_price * shares}
    new_trade = pd.DataFrame([new_trade])
    chatgpt_portfolio = pd.concat([chatgpt_portfolio, new_trade], ignore_index=True)
    cash = cash - shares * buy_price
    return cash, chatgpt_portfolio


#work in progress currently

def log_manual_sell(sell_price, shares_sold, ticker, cash, chatgpt_portfolio):
    if isinstance(chatgpt_portfolio, list):
        chatgpt_portfolio = pd.DataFrame(chatgpt_portfolio)
    if ticker not in chatgpt_portfolio["ticker"].values:
        raise KeyError(f"error, could not find {ticker} in portfolio")
    ticker_row = chatgpt_portfolio[chatgpt_portfolio['ticker'] == ticker]

    total_shares = int(ticker_row['shares'].item())
    print(total_shares)
    if shares_sold > total_shares:
        raise ValueError(f"You are trying to sell {shares_sold} but only own {total_shares}.")
    buy_price = float(ticker_row['buy_price'].item())
    
    reason = input("""Why are you selling? 
If this is a mistake, enter 1. """)

    if reason == "1": 
        raise SystemExit("Delete this function call from the program.")
    cost_basis = buy_price * shares_sold
    PnL = sell_price * shares_sold - cost_basis
    # leave buy fields empty
    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Bought": "",
        "Buy Price": "",
        "Cost Basis": cost_basis,
        "PnL": PnL,
        "Reason": f"MANUAL SELL - {reason}",
        "Shares Sold": shares_sold,
        "Sell Price": sell_price
    }
    file = "Scripts and CSV Files/chatgpt_trade_log.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(file, index=False) #check if ticker shares sold = total shares, if yes delete that row
    if total_shares == shares_sold:
        chatgpt_portfolio = chatgpt_portfolio[chatgpt_portfolio["ticker"] != ticker]
    else:
        ticker_row['shares'] = total_shares - shares_sold
        ticker_row['cost_basis'] = ticker_row['shares'] * ticker_row['buy_price']
        #return updated cash and updated portfolio
    cash = cash + shares_sold * sell_price
    return cash, chatgpt_portfolio

# This is where chatGPT gets daily updates from
# I give it data on its portfolio and also other tickers if requested
# Right now it additionally wants "^RUT", "IWO", and "XBI"

def daily_results(chatgpt_portfolio, cash):
    if isinstance(chatgpt_portfolio, pd.DataFrame):
            chatgpt_portfolio = chatgpt_portfolio.to_dict(orient="records")
    print(f"prices and updates for {today}")
    for stock in chatgpt_portfolio + [{"ticker": "^NSEI"}]:
        ticker = stock['ticker']
        try:
            data = yf.download(ticker, period="2d", progress=False)
            price = float(data['Close'].iloc[-1].item())
            last_price = float(data['Close'].iloc[-2].item())
            percent_change = ((price - last_price) / last_price) * 100
            volume = float(data['Volume'].iloc[-1].item())
        except Exception as e:
            raise KeyError(f"Download for {ticker} failed. Try checking internet connection.")
        print(f"{ticker} closing price: {price:.2f}")
        print(f"{ticker} volume for today: ₹{volume:,}")
        print(f"percent change from the day before: {percent_change:.2f}%")
    chatgpt_df = pd.read_csv("Scripts and CSV Files/chatgpt_portfolio_update.csv")

    # Filter TOTAL rows and get latest equity
    chatgpt_totals = chatgpt_df[chatgpt_df['Ticker'] == 'TOTAL'].copy() 
    chatgpt_totals['Date'] = pd.to_datetime(chatgpt_totals['Date'])
    final_date = chatgpt_totals['Date'].max()
    final_value = chatgpt_totals[chatgpt_totals['Date'] == final_date]
    final_equity = float(final_value['Total Equity'].values[0])
    print(final_equity)
    print(f"Latest ChatGPT Equity: ₹{final_equity:.2f}")

# Define start and end date for Nifty 50

# Get Nifty 50 data
    nifty = yf.download("^NSEI", start="2025-06-27", end=final_date + pd.Timedelta(days=1), progress=False)
    nifty = nifty.reset_index()[["Date", "Close"]]


# Normalize to ₹10000
    initial_price = nifty["Close"].iloc[0].item()
    price_now = nifty["Close"].iloc[-1].item()
    scaling_factor = 10000 / initial_price
    nifty_value = price_now * scaling_factor
    print(f"₹10000 Invested in the Nifty 50 Index: ₹{nifty_value:.2f}")
    print(f"today's portfolio: {chatgpt_portfolio}")
    print(f"cash balance: {cash}")



# === Run Portfolio ===
today = datetime.today().strftime('%Y-%m-%d')
chatgpt_portfolio = [
    {'ticker': 'ADANIENT.NS', 'shares': 200, 'buy_price': 100.0, 'stop_loss': 90.0, 'cost_basis': 20000.0},
    {'ticker': 'ADANIPORTS.NS', 'shares': 138, 'buy_price': 144.9, 'stop_loss': 130.41, 'cost_basis': 19996.2},
    {'ticker': 'APOLLOHOSP.NS', 'shares': 105, 'buy_price': 189.8, 'stop_loss': 170.82, 'cost_basis': 19929.0},
    {'ticker': 'ASIANPAINT.NS', 'shares': 85, 'buy_price': 234.69, 'stop_loss': 211.22, 'cost_basis': 19948.65},
    {'ticker': 'AXISBANK.NS', 'shares': 71, 'buy_price': 279.59, 'stop_loss': 251.63, 'cost_basis': 19850.89},
    {'ticker': 'BAJAJ-AUTO.NS', 'shares': 61, 'buy_price': 324.49, 'stop_loss': 292.04, 'cost_basis': 19793.89},
    {'ticker': 'BAJFINANCE.NS', 'shares': 54, 'buy_price': 369.39, 'stop_loss': 332.45, 'cost_basis': 19947.06},
    {'ticker': 'BAJAJFINSV.NS', 'shares': 48, 'buy_price': 414.29, 'stop_loss': 372.86, 'cost_basis': 19885.92},
    {'ticker': 'BEL.NS', 'shares': 44, 'buy_price': 459.18, 'stop_loss': 413.26, 'cost_basis': 20103.92},
    {'ticker': 'BHARTIARTL.NS', 'shares': 40, 'buy_price': 504.08, 'stop_loss': 453.67, 'cost_basis': 20163.2},
    {'ticker': 'CIPLA.NS', 'shares': 36, 'buy_price': 548.98, 'stop_loss': 494.08, 'cost_basis': 19763.28},
    {'ticker': 'COALINDIA.NS', 'shares': 33, 'buy_price': 593.88, 'stop_loss': 534.49, 'cost_basis': 19598.04},
    {'ticker': 'DRREDDY.NS', 'shares': 31, 'buy_price': 638.78, 'stop_loss': 574.9, 'cost_basis': 19802.18},
    {'ticker': 'EICHERMOT.NS', 'shares': 29, 'buy_price': 683.67, 'stop_loss': 615.3, 'cost_basis': 19826.43},
    {'ticker': 'ETERNAL.NS', 'shares': 27, 'buy_price': 728.57, 'stop_loss': 655.71, 'cost_basis': 19671.39},
    {'ticker': 'GRASIM.NS', 'shares': 25, 'buy_price': 773.47, 'stop_loss': 696.12, 'cost_basis': 19336.75},
    {'ticker': 'HCLTECH.NS', 'shares': 24, 'buy_price': 818.37, 'stop_loss': 736.53, 'cost_basis': 19640.88},
    {'ticker': 'HDFCBANK.NS', 'shares': 23, 'buy_price': 863.27, 'stop_loss': 776.94, 'cost_basis': 19855.21},
    {'ticker': 'HDFCLIFE.NS', 'shares': 22, 'buy_price': 908.16, 'stop_loss': 817.34, 'cost_basis': 19979.52},
    {'ticker': 'HEROMOTOCO.NS', 'shares': 21, 'buy_price': 953.06, 'stop_loss': 857.75, 'cost_basis': 20014.26},
    {'ticker': 'HINDALCO.NS', 'shares': 20, 'buy_price': 997.96, 'stop_loss': 898.16, 'cost_basis': 19959.2},
    {'ticker': 'HINDUNILVR.NS', 'shares': 19, 'buy_price': 1042.86, 'stop_loss': 938.57, 'cost_basis': 19814.34},
    {'ticker': 'ICICIBANK.NS', 'shares': 18, 'buy_price': 1087.76, 'stop_loss': 978.98, 'cost_basis': 19579.68},
    {'ticker': 'INDUSINDBK.NS', 'shares': 17, 'buy_price': 1132.65, 'stop_loss': 1019.39, 'cost_basis': 19255.05},
    {'ticker': 'INFY.NS', 'shares': 16, 'buy_price': 1177.55, 'stop_loss': 1059.8, 'cost_basis': 18840.8},
    {'ticker': 'ITC.NS', 'shares': 16, 'buy_price': 1222.45, 'stop_loss': 1100.21, 'cost_basis': 19559.2},
    {'ticker': 'JIOFIN.NS', 'shares': 15, 'buy_price': 1267.35, 'stop_loss': 1140.62, 'cost_basis': 19010.25},
    {'ticker': 'JSWSTEEL.NS', 'shares': 15, 'buy_price': 1312.24, 'stop_loss': 1180.02, 'cost_basis': 19683.6},
    {'ticker': 'KOTAKBANK.NS', 'shares': 14, 'buy_price': 1357.14, 'stop_loss': 1221.43, 'cost_basis': 18999.96},
    {'ticker': 'LT.NS', 'shares': 14, 'buy_price': 1402.04, 'stop_loss': 1261.84, 'cost_basis': 19628.56},
    {'ticker': 'M&M.NS', 'shares': 13, 'buy_price': 1446.94, 'stop_loss': 1302.25, 'cost_basis': 18810.22},
    {'ticker': 'MARUTI.NS', 'shares': 13, 'buy_price': 1491.84, 'stop_loss': 1342.66, 'cost_basis': 19393.92},
    {'ticker': 'NESTLEIND.NS', 'shares': 12, 'buy_price': 1536.73, 'stop_loss': 1383.06, 'cost_basis': 18440.76},
    {'ticker': 'NTPC.NS', 'shares': 12, 'buy_price': 1581.63, 'stop_loss': 1423.47, 'cost_basis': 18979.56},
    {'ticker': 'ONGC.NS', 'shares': 12, 'buy_price': 1626.53, 'stop_loss': 1463.88, 'cost_basis': 19518.36},
    {'ticker': 'POWERGRID.NS', 'shares': 11, 'buy_price': 1671.43, 'stop_loss': 1504.29, 'cost_basis': 18385.73},
    {'ticker': 'RELIANCE.NS', 'shares': 11, 'buy_price': 1716.33, 'stop_loss': 1544.7, 'cost_basis': 18879.63},
    {'ticker': 'SBILIFE.NS', 'shares': 11, 'buy_price': 1761.22, 'stop_loss': 1585.1, 'cost_basis': 19373.42},
    {'ticker': 'SHRIRAMFIN.NS', 'shares': 10, 'buy_price': 1806.12, 'stop_loss': 1625.51, 'cost_basis': 18061.2},
    {'ticker': 'SBIN.NS', 'shares': 10, 'buy_price': 1851.02, 'stop_loss': 1665.92, 'cost_basis': 18510.2},
    {'ticker': 'SUNPHARMA.NS', 'shares': 10, 'buy_price': 1895.92, 'stop_loss': 1706.33, 'cost_basis': 18959.2},
    {'ticker': 'TCS.NS', 'shares': 9, 'buy_price': 1940.82, 'stop_loss': 1746.74, 'cost_basis': 17467.38},
    {'ticker': 'TATACONSUM.NS', 'shares': 9, 'buy_price': 1985.71, 'stop_loss': 1787.14, 'cost_basis': 17871.39},
    {'ticker': 'TATAMOTORS.NS', 'shares': 9, 'buy_price': 2030.61, 'stop_loss': 1827.55, 'cost_basis': 18275.49},
    {'ticker': 'TATASTEEL.NS', 'shares': 9, 'buy_price': 2075.51, 'stop_loss': 1867.96, 'cost_basis': 18679.59},
    {'ticker': 'TECHM.NS', 'shares': 8, 'buy_price': 2120.41, 'stop_loss': 1908.37, 'cost_basis': 16963.28},
    {'ticker': 'TITAN.NS', 'shares': 8, 'buy_price': 2165.31, 'stop_loss': 1948.78, 'cost_basis': 17322.48},
    {'ticker': 'TRENT.NS', 'shares': 8, 'buy_price': 2210.2, 'stop_loss': 1989.18, 'cost_basis': 17681.6},
    {'ticker': 'ULTRACEMCO.NS', 'shares': 8, 'buy_price': 2255.1, 'stop_loss': 2029.59, 'cost_basis': 18040.8},
    {'ticker': 'WIPRO.NS', 'shares': 8, 'buy_price': 2299.0, 'stop_loss': 2069.1, 'cost_basis': 18392.0}
]
chatgpt_portfolio = pd.DataFrame(chatgpt_portfolio)
# === TODO ===
#nothing

cash = 44000.0
print("--- Processing portfolio ---")
chatgpt_portfolio, cash = process_portfolio(chatgpt_portfolio, cash)
print("--- Generating daily results ---")
daily_results(chatgpt_portfolio, cash)