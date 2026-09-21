# ============================================================
# STRATEGY SHOWDOWN v2
# 3 popular trading strategies x 4 markets vs buy-and-hold
# Paste this whole thing into ONE Google Colab cell and run it.
# ============================================================

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
# RULES - LOCKED IN BEFORE LOOKING AT RESULTS
# (Standard textbook settings. Don't tweak these to make a strategy "win" -
#  that's overfitting.)
# ============================================================
MARKETS = {
    "ASX 200 (IOZ)":    "IOZ.AX",
    "S&P 500 (IVV)":    "IVV.AX",
    "Nasdaq 100 (NDQ)": "NDQ.AX",
    "Gold (GOLD)":      "GOLD.AX",
}
COST_PER_TRADE = 0.001   # 0.1% on every buy and every sell
START_MONEY = 10_000
WARMUP = 200             # days skipped at the start so every strategy starts on the same day

# ============================================================
# THE 3 STRATEGIES
# Each returns a Series: 1 = hold the ETF, 0 = sit in cash
# ============================================================
def sma_crossover(price):
    """Trend following: hold when 50-day average is above 200-day average."""
    return (price.rolling(50).mean() > price.rolling(200).mean()).astype(int)

def rsi(price, n=14):
    delta = price.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)

def rsi_oversold(price):
    """Mean reversion: buy when RSI(14) drops below 30 ('oversold'),
    sell when it rises above 70 ('overbought')."""
    r = rsi(price)
    sig = pd.Series(np.nan, index=price.index)
    sig[r < 30] = 1
    sig[r > 70] = 0
    return sig.ffill().fillna(0).astype(int)

def breakout(price):
    """Turtle-style breakout: buy when price closes above its previous 55-day high,
    sell when it closes below its previous 20-day low."""
    high55 = price.rolling(55).max().shift(1)
    low20 = price.rolling(20).min().shift(1)
    sig = pd.Series(np.nan, index=price.index)
    sig[price > high55] = 1
    sig[price < low20] = 0
    return sig.ffill().fillna(0).astype(int)

STRATEGIES = {
    "SMA 50/200":   sma_crossover,
    "RSI oversold": rsi_oversold,
    "Breakout 55/20": breakout,
}

# ============================================================
# BACKTEST ENGINE
# ============================================================
def run_backtest(price, signal):
    ret = price.pct_change().fillna(0)
    position = signal.shift(1).fillna(0)          # trade the day AFTER the signal
    trades = position.diff().abs().fillna(0)
    strat_ret = position * ret - trades * COST_PER_TRADE
    return strat_ret, int(trades.sum()), position.mean()

def score(daily_ret):
    equity = START_MONEY * (1 + daily_ret).cumprod()
    years = len(daily_ret) / 252
    cagr = (equity.iloc[-1] / START_MONEY) ** (1 / years) - 1
    vol = daily_ret.std() * np.sqrt(252)
    sharpe = (daily_ret.mean() * 252) / vol if vol > 0 else np.nan
    max_dd = (equity / equity.cummax() - 1).min()
    return equity, {"Final $": equity.iloc[-1], "CAGR": cagr,
                    "Sharpe": sharpe, "Max drop": max_dd}

# ============================================================
# RUN EVERYTHING
# ============================================================
rows = []
equity_curves = {}

for market, ticker in MARKETS.items():
    hist = yf.Ticker(ticker).history(period="10y", auto_adjust=True)
    if hist.empty:
        print(f"!! No data for {ticker}, skipping")
        continue
    full_price = hist["Close"]
    full_price.index = full_price.index.tz_localize(None)

    # Build signals on full history, then trim warm-up so all start on the same day
    signals = {name: fn(full_price) for name, fn in STRATEGIES.items()}
    price = full_price.iloc[WARMUP:]
    period = f"{price.index[0].date()} to {price.index[-1].date()}"
    print(f"{market}: {period}")

    curves = {}
    bh_ret = price.pct_change().fillna(0)
    bh_eq, bh_stats = score(bh_ret)
    curves["Buy & Hold"] = bh_eq
    rows.append({"Market": market, "Strategy": "Buy & Hold", **bh_stats,
                 "Trades": 1, "Time in mkt": 1.0, "Beat B&H?": "-"})

    for name, sig in signals.items():
        s_ret, n_trades, t_in = run_backtest(price, sig.iloc[WARMUP:])
        eq, st = score(s_ret)
        curves[name] = eq
        beat = "YES" if st["Final $"] > bh_stats["Final $"] else "no"
        rows.append({"Market": market, "Strategy": name, **st,
                     "Trades": n_trades, "Time in mkt": t_in, "Beat B&H?": beat})

    equity_curves[market] = curves

results = pd.DataFrame(rows)

# ============================================================
# SCOREBOARD
# ============================================================
show = results.copy()
show["Final $"] = show["Final $"].map("${:,.0f}".format)
show["CAGR"] = show["CAGR"].map("{:.2%}".format)
show["Sharpe"] = show["Sharpe"].map("{:.2f}".format)
show["Max drop"] = show["Max drop"].map("{:.1%}".format)
show["Time in mkt"] = show["Time in mkt"].map("{:.0%}".format)

print("\n" + "=" * 90)
print("SCOREBOARD - $10,000 starting in each")
print("=" * 90)
for market in show["Market"].unique():
    print(f"\n{market}")
    print(show[show["Market"] == market].drop(columns="Market").to_string(index=False))

tests = results[results["Strategy"] != "Buy & Hold"]
wins = (tests["Beat B&H?"] == "YES").sum()
print("\n" + "=" * 90)
print(f"VERDICT: {wins} of {len(tests)} strategy tests beat simply buying and holding.")
print("=" * 90)
print("Notes: 0.1% cost per trade. Cash earns 0% when out of the market. Tax ignored.")

# ============================================================
# CHART 1: growth of $10k, one panel per market
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
for ax, (market, curves) in zip(axes.flat, equity_curves.items()):
    for name, eq in curves.items():
        style = {"linewidth": 2.2, "color": "black"} if name == "Buy & Hold" else {"linewidth": 1.2}
        ax.plot(eq.index, eq, label=name, **style)
    ax.set_title(market)
    ax.set_ylabel("$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
fig.suptitle("Growth of $10,000: 3 strategies vs Buy & Hold (black)", fontsize=14)
plt.tight_layout()
plt.show()

# ============================================================
# CHART 2: yearly return gap vs buy-and-hold (above 0 = strategy won)
# ============================================================
bh_cagr = results[results["Strategy"] == "Buy & Hold"].set_index("Market")["CAGR"]
gap = tests.copy()
gap["Gap"] = gap.apply(lambda r: (r["CAGR"] - bh_cagr[r["Market"]]) * 100, axis=1)
pivot = gap.pivot(index="Market", columns="Strategy", values="Gap")

ax = pivot.plot(kind="bar", figsize=(12, 5), width=0.75)
ax.axhline(0, color="black", linewidth=1)
ax.set_ylabel("Yearly return vs Buy & Hold (% points)")
ax.set_title("How much each strategy beat (+) or lost to (-) Buy & Hold per year")
ax.set_xlabel("")
plt.xticks(rotation=0)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
