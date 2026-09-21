# Does a Moving Average Crossover Beat Buy-and-Hold?

A backtest of the popular **50/200-day moving average crossover** trading strategy against simply buying and holding, tested on two markets over roughly 9 years (July 2017 – September 2026):

- **IOZ**: iShares Core S&P/ASX 200 ETF (Australian shares)
- **IVV**: iShares S&P 500 ETF (US shares, ASX-listed, priced in AUD)

## TL;DR

The strategy lost to buy-and-hold in **both** markets, on raw returns *and* on risk-adjusted returns. It also failed to reduce the worst drawdown, which is the main reason people use it.

| Market | Buy & Hold | SMA 50/200 Strategy | Gap |
|---|---|---|---|
| ASX 200 (IOZ) | $10k → **$21,609** | $10k → **$9,676** | −$11,933 |
| S&P 500 (IVV) | $10k → **$38,440** | $10k → **$25,995** | −$12,445 |

## The Strategy

- **Buy** when the 50-day moving average crosses above the 200-day moving average
- **Sell to cash** when the 50-day crosses back below the 200-day
- Trades are executed the **day after** the signal, to avoid look-ahead bias (you only know the signal after the market closes)
- A **0.1% cost** is charged on every buy and sell to cover brokerage and spread
- Prices are **dividend-adjusted**, so buy-and-hold gets credit for reinvested dividends
- Both approaches start on the same date, after the 200-day warm-up period

## Results

### ASX 200 (IOZ)

| Metric | Buy & Hold | SMA 50/200 |
|---|---|---|
| Final value | $21,609 | $9,676 |
| Total return | 116.1% | −3.2% |
| Yearly return (CAGR) | 8.69% | −0.36% |
| Volatility (yearly) | 14.5% | 12.3% |
| Sharpe ratio | 0.65 | 0.03 |
| Max drawdown | −35.7% | −35.8% |

15 trades, in the market 81% of the time.

![IOZ results](ioz_1.png.png)
![IOZ trades and drawdown](ioz_2.png.png)

### S&P 500 (IVV)

| Metric | Buy & Hold | SMA 50/200 |
|---|---|---|
| Final value | $38,440 | $25,995 |
| Total return | 284.4% | 159.9% |
| Yearly return (CAGR) | 15.67% | 10.88% |
| Volatility (yearly) | 14.6% | 13.1% |
| Sharpe ratio | 1.07 | 0.85 |
| Max drawdown | −23.9% | −23.9% |

11 trades, in the market 84% of the time.

![IVV results](ivv_1.png.png)
![IVV trades and drawdown](ivv_2.png.png)

## Key Findings

**1. Fast crashes break the strategy.** In the March 2020 COVID crash, prices fell so quickly that the 50-day average didn't cross below the 200-day until the crash was nearly over. The strategy rode the full fall, sold near the bottom, then bought back only after the recovery. On IOZ this single event wiped out most of its gains, and it never caught up.

**2. Whipsaws add up.** In choppy markets (IOZ in 2022, IVV in 2025–2026), the strategy repeatedly sold after a dip and bought back higher once the market rebounded. Each round trip locked in a loss.

**3. It works in slow bear markets.** The one clear win was the S&P 500 in 2022. That decline was a slow grind rather than a crash, so the strategy exited early, capped its drawdown at about 10% while buy-and-hold fell about 20%, and re-entered near the same price.

**4. No crash protection when it mattered.** The worst drawdown was essentially identical to buy-and-hold in both markets (−35.8% vs −35.7% on IOZ, −23.9% vs −23.9% on IVV), so the strategy gave up returns without delivering the protection that is its main selling point.

**Takeaway:** a 50/200 crossover can help in slow, drawn-out declines, but it reacts too late to fast crashes and V-shaped recoveries. Recent markets have mostly featured the latter, so over this period, doing nothing beat trading.

## Limitations

- When out of the market the strategy earns 0%. Real cash would earn interest, but at ~19% time in cash this would not close the gap.
- Taxes are ignored. Frequent selling would likely make the strategy look *worse* after capital gains tax.
- IVV is priced in AUD, so its results include AUD/USD currency movements.
- One parameter set (50/200) was tested on purpose. Tuning the averages until something "wins" on past data risks overfitting, where a strategy looks great historically but fails going forward.
- Past performance does not predict future results. This is a learning project, not financial advice.

## How to Run

1. Open [Google Colab](https://colab.research.google.com) and create a new notebook
2. Paste the contents of `ioz_backtest.py` or `ivv_backtest.py` into a cell
3. Run it. Data is downloaded automatically from Yahoo Finance, so no dataset upload is needed

To test other ideas, change `TICKER`, `SHORT_MA`, `LONG_MA` or `COST_PER_TRADE` at the top of the script.

## Tools

Python · pandas · NumPy · Matplotlib · yfinance · Google Colab

## Author

**Aaron Durom**, Bachelor of Business Analytics (Deakin University), currently studying a Master of Cyber Security.
