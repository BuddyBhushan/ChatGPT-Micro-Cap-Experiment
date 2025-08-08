import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

# === Load and prepare ChatGPT portfolio ===
chatgpt_df = pd.read_csv("Scripts and CSV files/chatgpt_portfolio_update.csv")
chatgpt_totals = chatgpt_df[chatgpt_df['Ticker'] == 'TOTAL'].copy()
chatgpt_totals['Date'] = pd.to_datetime(chatgpt_totals['Date'])

# Add fake baseline row for June 27 (weekend)
baseline_date = pd.Timestamp("2025-06-27")
baseline_equity = 10000  # Starting value
baseline_chatgpt_row = pd.DataFrame({
    "Date": [baseline_date],
    "Total Equity": [baseline_equity]   
    })
chatgpt_totals = pd.concat([baseline_chatgpt_row, chatgpt_totals], ignore_index=True).sort_values("Date")

# === Download and prepare Nifty 50 ===
start_date = baseline_date
end_date = chatgpt_totals['Date'].max()

nifty = yf.download("^NSEI", start=start_date, end=end_date + pd.Timedelta(days=1), progress=False)
nifty = nifty.reset_index()

# Fix columns if downloaded with MultiIndex
if isinstance(nifty.columns, pd.MultiIndex):
    nifty.columns = nifty.columns.get_level_values(0)
# Real close prices on June 27 (pulled from YF)
nifty_27_price = 24000.00

# Normalize to ₹10000 baseline
nifty_scaling_factor = 10000 / nifty_27_price
# create adjusted close col



nifty["Nifty Value (₹10000 Invested)"] = nifty["Close"] * nifty_scaling_factor

# === Plot ===
plt.figure(figsize=(10, 6))
plt.style.use("seaborn-v0_8-whitegrid")
plt.plot(chatgpt_totals['Date'], chatgpt_totals["Total Equity"], label="ChatGPT (₹10000 Invested)", marker="o", color="blue", linewidth=2)
plt.plot(nifty['Date'], nifty["Nifty Value (₹10000 Invested)"], label="Nifty 50 (₹10000 Invested)", marker="o", color="orange", linestyle='--', linewidth=2)

final_date = chatgpt_totals['Date'].iloc[-1]
final_chatgpt = float(chatgpt_totals["Total Equity"].iloc[-1])
final_nifty = nifty["Nifty Value (₹10000 Invested)"].iloc[-1]

plt.text(final_date, final_chatgpt + 0.3, f"+{final_chatgpt - 10000:.1f}%", color="blue", fontsize=9)
plt.text(final_date, final_nifty + 0.9, f"+{final_nifty - 10000:.1f}%", color="orange", fontsize=9)

plt.title("ChatGPT's Micro Cap Portfolio vs. Nifty 50")
plt.xlabel("Date")
plt.ylabel("Value of ₹10000 Investment")
plt.xticks(rotation=15)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()