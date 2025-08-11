# BTC 30-Day Sprint

## Quickstart

Clone the repo and activate your virtual environment:

```bash
git clone https://github.com/PeytonAllworth/btc-30-day.git
cd btc-30-day
source venv/bin/activate

https://asciinema.org/a/SRwYGcXmwcruUrvzHVSNzCUUs

### Demo Vid of my mempool_ping.py

[Watch CLI in Action](https://asciinema.org/a/SRwYGcXmwcruUrvzHVSNzCUUs)

## MARA Miner Valuation Project

### Allworth Core Mining P/E (ACMPE)

ACMPE is my custom valuation multiple for Bitcoin miners. It answers a simple question:
**"Ignoring the balance-sheet BTC stack and financing noise, how expensive is the mining business?"**

ACMPE strips out BTC price swings from earnings and neutralizes capital structure (debt), so we're valuing operations, not coin holdings.

#### Why not use regular P/E?

For miners like MARA, standard P/E is whiplash:
- **BTC goes up** → big accounting gains → P/E looks cheap
- **BTC goes down** → big losses → P/E looks broken

ACMPE fixes this by removing those BTC revaluation swings and adding back interest (since we account for debt elsewhere). Think of it as a clean, operations-only P/E.

#### Two Moving Parts

**1) mNAV (context)**
- Treasury = BTC holdings × live BTC price
- NAV = Treasury + Cash − Debt  
- mNAV = Market Cap ÷ Treasury

This tells you if the stock trades near/above/below the value of the coins it holds.

**2) ACMPE (the operating multiple)**
- Residual Business Value (RBV) = Market Cap − NAV
- What the market is paying for the business, after backing out the BTC stack, cash, and debt
- Core earnings (per quarter) = Net Income − BTC Revaluation + Interest Expense

Remove BTC price moves from earnings, and add back interest so we're not double-penalizing debt (we already subtract debt in NAV).

**ACMPE-TTM = RBV ÷ (sum of Core over the last 4 aligned quarters)**

If we don't have 4 clean quarters yet, we show ACMPE-RunRate = RBV ÷ (last Core × 4) and label it as such.

#### What exactly is "BTC Revaluation"?

It's the income-statement line like "Change in fair value of digital assets (and receivable), net."

- **Post-ASU (2025+)**: we subtract the full revaluation (gains or losses)
- **Pre-ASU (<2025)**: companies didn't book BTC gains in NI, only impairments. To stay honest, we remove losses only (i.e., reval_used = min(estimated_reval, 0)), and we do not subtract synthetic gains

When the exact P&L line isn't available, we estimate quarterly revaluation with balance-sheet deltas:
**ΔFairValue − ΔCost** between consecutive quarter-ends.

#### "Add back interest" (plain English)

Net Income already deducts interest. But we also remove debt from NAV. If we left interest inside and subtracted debt in NAV, we'd punish leverage twice. So we add interest back in the Core calculation to make earnings capital-structure neutral (closer to EBIT after de-BTC-ifying).

#### How to read ACMPE

- **Lower ACMPE** → the mining operations are cheaper relative to the business value (RBV)
- **Higher ACMPE** → pricier operations  
- **N/A (negative core)** → after normalization, the last 4 quarters of Core sum to ≤ 0, so a P/E-style multiple isn't meaningful. You can still watch mNAV and the Core table to see what's driving it

#### Simple Decision Gate (tunable)

- **BUY** if mNAV ≤ 0.95× and ACMPE-TTM ≤ ~18× and NAV > 0
- **HOLD/AVOID** if mNAV > 1.10×
- **Else NEUTRAL**

#### Worked Mini-Example (numbers rounded)

Say:
- Market Cap = $5.70B
- Treasury = $6.16B (BTC units × live price)
- Cash = $0.11B  
- Debt = $2.60B
- NAV = 6.16 + 0.11 − 2.60 = $3.67B
- RBV = 5.70 − 3.67 = $2.03B

Four quarters of Core = NI − Reval + Interest:
- Q1: +$15.1M
- Q2: +$170.5M  
- Q3: −$13.2M
- Q4: −$371.5M

**Core TTM = 15.1 + 170.5 − 13.2 − 371.5 ≈ −$199.2M → negative**

**ACMPE-TTM = N/A (negative core)**

You'd lean on mNAV and the per-quarter Core table until Core turns positive.

#### Guardrails & Transparency

- Align by quarter end. Never mix periods
- Label sources. If we used manual overrides while SEC data lags, the report says so
- No BTC repricing of earnings. BTC's live price is for Treasury/NAV only. Earnings stay in USD; we remove BTC swings via revaluation
- Post-ASU vs pre-ASU rules are enforced every run

#### One-Liner (use in email)

**ACMPE (Allworth Core Mining P/E) = RBV ÷ Core TTM, where Core = Net Income − BTC Revaluation + Interest. It prices the mining business itself—stripping out BTC price noise and neutralizing leverage—so you can judge operational value, not balance-sheet luck.**

## PRIME mNAV (Peyton's Risk-Integrated Miner mNAV)
I adjust mNAV by an operations P/E view:
Fair mNAV = (Treasury + Cash − Debt + PE × Core TTM) ÷ Treasury
Where Core TTM = sum over 4q of (Net Income − BTC Revaluation + Interest), Ops-Only.
I show scenarios (Value 5× / Market 8× / Growth 11×). If Core TTM ≤ 0, PE × Core is negative.

### Project Files

- **`mara_val_redo.py`** - Simple MARA valuation tool with ACMPE calculation
- **`mara_val.py`** - Full-featured version with SEC data fetching and policy enforcement
- **`overrides/core_quarters.json`** - Manual quarterly data for when SEC data lags

### Usage

```bash
# Simple version (recommended for daily use)
python3 mara_val_redo.py

# Full version with SEC data (when you need detailed analysis)
python3 mara_val.py

# Use manual overrides (when SEC data doesn't align)
OVERRIDE_MODE=1 python3 mara_val.py
```


