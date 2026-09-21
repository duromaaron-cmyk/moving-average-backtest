# ============================================================
# IVV (iShares S&P 500 ETF) - Moving Average Crossover Backtest
# Paste this whole thing into ONE Google Colab cell and run it.
# ============================================================

# --- Setup: yfinance is usually pre-installed in Colab, this makes sure ---
try:
    import yfinance as yf
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "yfinance"])
    import yfinance as yf

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SETTINGS - change these to test different ideas
# ============================================================
TICKER = "IVV.AX"      # iShares S&P 500 ETF, ASX-listed (priced in AUD)
SHORT_MA = 50          # fast moving average (days)
LONG_MA = 200          # slow moving average (days)
COST_PER_TRADE = 0.001 # 0.1% cost each time you buy or sell (brokerage + spread)
START_MONEY = 10_000   # starting amount in dollars

# ============================================================
# 1. PULL THE DATA
# ============================================================
# auto_adjust=True means prices include dividends reinvested,
# which is fair to buy-and-hold (ASX ETFs pay a lot of dividends).
hist = yf.Ticker(TICKER).history(period="10y", auto_adjust=True)
if hist.empty:
    raise SystemExit("No data came back. Check the ticker or try again in a minute.")

df = pd.DataFrame({"price": hist["Close"]})
df.index = df.index.tz_localize(None)
print(f"Got {len(df)} trading days: {df.index[0].date()} to {df.index[-1].date()}")

# ============================================================
# 2. BUILD THE STRATEGY
# ============================================================
df["sma_short"] = df["price"].rolling(SHORT_MA).mean()
df["sma_long"] = df["price"].rolling(LONG_MA).mean()

# In the market (1) when the fast average is above the slow one, else cash (0)
df["signal"] = (df["sma_short"] > df["sma_long"]).astype(int)

# Skip the warm-up period so both approaches start on the same day
df = df.dropna().copy()

# Daily % change in the ETF price
df["mkt_ret"] = df["price"].pct_change().fillna(0)

# IMPORTANT: use yesterday's signal for today's return.
# You only know the signal after the close, so you can't trade on it the same day.
# Skipping this step is the #1 beginner mistake - it makes results look amazing but fake.
df["position"] = df["signal"].shift(1).fillna(0)

# Charge a cost on every day the position changes (a buy or a sell)
df["trade"] = df["position"].diff().abs().fillna(0)
df["strat_ret"] = df["position"] * df["mkt_ret"] - df["trade"] * COST_PER_TRADE

# Grow $START_MONEY with each approach
df["buy_hold"] = START_MONEY * (1 + df["mkt_ret"]).cumprod()
df["strategy"] = START_MONEY * (1 + df["strat_ret"]).cumprod()

# ============================================================
# 3. SCORECARD
# ============================================================
def stats(daily_returns, equity):
    years = len(daily_returns) / 252
    total = equity.iloc[-1] / START_MONEY - 1
    cagr = (equity.iloc[-1] / START_MONEY) ** (1 / years) - 1
    vol = daily_returns.std() * np.sqrt(252)
    sharpe = (daily_returns.mean() * 252) / vol if vol > 0 else np.nan
    max_dd = (equity / equity.cummax() - 1).min()
    return {
        "Final value": f"${equity.iloc[-1]:,.0f}",
        "Total return": f"{total:.1%}",
        "Yearly return (CAGR)": f"{cagr:.2%}",
        "Volatility (yearly)": f"{vol:.1%}",
        "Sharpe ratio": f"{sharpe:.2f}",
        "Worst drop (max drawdown)": f"{max_dd:.1%}",
    }

results = pd.DataFrame({
    "Buy & Hold": stats(df["mkt_ret"], df["buy_hold"]),
    f"SMA {SHORT_MA}/{LONG_MA}": stats(df["strat_ret"], df["strategy"]),
})

n_trades = int(df["trade"].sum())
time_in = df["position"].mean()

print("\n" + "=" * 55)
print(f"RESULTS: {TICKER}, {df.index[0].date()} to {df.index[-1].date()}")
print("=" * 55)
print(results.to_string())
print(f"\nStrategy made {n_trades} trades and was in the market {time_in:.0%} of the time.")
print("Note: when out of the market the strategy earns 0% (no cash interest), and tax is ignored.")

# ============================================================
# 4. CHARTS
# ============================================================
fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True,
                         gridspec_kw={"height_ratios": [2, 2, 1]})

# Chart 1: growth of $10k
axes[0].plot(df.index, df["buy_hold"], label="Buy & Hold", linewidth=1.5)
axes[0].plot(df.index, df["strategy"], label=f"SMA {SHORT_MA}/{LONG_MA}", linewidth=1.5)
axes[0].set_title(f"Growth of ${START_MONEY:,}")
axes[0].set_ylabel("$")
axes[0].legend()
axes[0].grid(alpha=0.3)

# Chart 2: price, moving averages, buy/sell points
buys = df[df["position"].diff() == 1]
sells = df[df["position"].diff() == -1]
axes[1].plot(df.index, df["price"], label=f"{TICKER} price", color="grey", linewidth=1)
axes[1].plot(df.index, df["sma_short"], label=f"{SHORT_MA}-day avg", linewidth=1)
axes[1].plot(df.index, df["sma_long"], label=f"{LONG_MA}-day avg", linewidth=1)
axes[1].scatter(buys.index, buys["price"], marker="^", color="green", s=80, label="Buy", zorder=5)
axes[1].scatter(sells.index, sells["price"], marker="v", color="red", s=80, label="Sell", zorder=5)
axes[1].set_title("Price with moving averages and trades")
axes[1].legend()
axes[1].grid(alpha=0.3)

# Chart 3: drawdowns (how far below the previous peak)
axes[2].fill_between(df.index, (df["buy_hold"] / df["buy_hold"].cummax() - 1) * 100,
                     0, alpha=0.4, label="Buy & Hold")
axes[2].fill_between(df.index, (df["strategy"] / df["strategy"].cummax() - 1) * 100,
                     0, alpha=0.4, label="Strategy")
axes[2].set_title("Drawdown (% below previous high)")
axes[2].set_ylabel("%")
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.show()
