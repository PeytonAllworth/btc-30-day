#!/usr/bin/env python3
"""
Simple MARA Valuation Tool
Just mNAV and ACMPE-TTM. That's it.
"""

import requests
import yfinance as yf
import json
import os

# Environment variables
USE_ADJUSTMENTS = os.getenv("USE_ADJUSTMENTS", "1") == "1"
ADD_BACK_SBC = os.getenv("ADD_BACK_SBC", "0") == "1"
OPS_ONLY = os.getenv("OPS_ONLY", "1") == "1"
ADJ_PATH = os.getenv("ADJ_PATH", "overrides/adjustments.json")
FAIR_PE = float(os.getenv("FAIR_PE", "8"))  # pick 5/8/11 per scenario when printing

# Manual quarterly data for ACMPE calculation
MARA_QUARTERS = [
    {
        "period": "2024-09-30",
        "ni": 12_725_000,
        "reval_used": 0,  # pre-ASU: only remove downside
        "interest": 2_342_000,
        "policy": "pre-ASU"
    },
    {
        "period": "2024-12-31", 
        "ni": 162_470_667,
        "reval_used": 0,  # pre-ASU: only remove downside
        "interest": 8_033_000,
        "policy": "pre-ASU"
    },
    {
        "period": "2025-03-31",
        "ni": -533_443_000,
        "reval_used": -510_267_000,  # post-ASU: full reval
        "interest": 9_941_000,
        "policy": "post-ASU"
    },
    {
        "period": "2025-06-30",
        "ni": 808_235_000,
        "reval_used": 1_192_574_000,  # post-ASU: full reval
        "interest": 12_835_000,
        "policy": "post-ASU"
    }
]

def apply_policy(period: str, reval_used: float) -> float:
    """Enforce pre/post-ASU revaluation rules"""
    return reval_used if period >= "2025-01-01" else min(reval_used, 0.0)

def get_cash_and_debt():
    """Get live cash and debt from Yahoo Finance"""
    try:
        mara = yf.Ticker("MARA")
        bs = mara.quarterly_balance_sheet
        
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]
            cash = float(latest.get("Cash And Cash Equivalents", latest.get("Cash", 0.0)) or 0.0)
            debt = float(latest.get("Total Debt", latest.get("Long Term Debt", 0.0)) or 0.0)
            
            if cash > 0 and debt > 0:
                return cash, debt
            else:
                print("❌ Yahoo Finance returned incomplete cash/debt data")
                return None, None
        else:
            print("❌ Yahoo Finance returned no balance sheet data")
            return None, None
    except Exception as e:
        print(f"❌ Error fetching cash/debt: {e}")
        return None, None

def load_adjustments(path=ADJ_PATH):
    """Load and validate adjustments from JSON file"""
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path) as f:
            rows = json.load(f)
        
        out = {}
        for r in rows:
            # Validate required fields
            if not all(k in r for k in ["period", "label", "reason", "category"]):
                print(f"⚠️  Skipping invalid adjustment: missing required fields")
                continue
            
            # Reject BTC revaluation adjustments (double-counting protection)
            if any(word in r["label"].lower() for word in ["btc", "crypto", "digital asset", "revaluation", "fair value"]):
                print(f"⚠️  Skipping BTC revaluation adjustment: {r['label']}")
                continue
            
            # Validate category
            valid_categories = ["financing", "transaction", "restructuring", "litigation", "asset_sale", "future", "growth", "preop", "debt", "other"]
            if r["category"] not in valid_categories:
                print(f"⚠️  Skipping adjustment with invalid category '{r['category']}': {r['label']}")
                continue
            
            p = r["period"]
            v = float(r["impact_on_core"])
            out.setdefault(p, []).append({
                "label": r["label"],
                "impact": v,
                "reason": r["reason"],
                "category": r["category"]
            })
        return out
    except Exception as e:
        print(f"⚠️  Failed to load adjustments: {e}")
        return {}

def get_btc_price():
    """Get current BTC price from CoinGecko"""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        return response.json()["bitcoin"]["usd"]
    except:
        return None

def get_mara_market_cap():
    """Get MARA market cap from Yahoo Finance"""
    try:
        print("🔍 Fetching MARA data from Yahoo Finance...")
        mara = yf.Ticker("MARA")
        
        # Try to get basic info first
        print("   Getting basic info...")
        info = mara.info
        print(f"   Info keys available: {list(info.keys())[:10]}...")
        
        # Try multiple ways to get market cap
        market_cap = info.get("marketCap")
        if market_cap and market_cap > 0:
            print(f"✅ Got market cap from info: ${market_cap:,.0f}")
            return market_cap
        
        # Alternative: calculate from price * shares
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        shares_outstanding = info.get("sharesOutstanding")
        
        print(f"   Current price: ${current_price if current_price else 'N/A'}")
        print(f"   Shares outstanding: {shares_outstanding if shares_outstanding else 'N/A'}")
        
        if current_price and shares_outstanding:
            calculated_mc = current_price * shares_outstanding
            print(f"✅ Calculated market cap: ${calculated_mc:,.0f}")
            return calculated_mc
        
        # Try fast info as last resort
        print("   Trying fast info...")
        fast_info = mara.fast_info
        if hasattr(fast_info, 'market_cap') and fast_info.market_cap:
            print(f"✅ Got market cap from fast info: ${fast_info.market_cap:,.0f}")
            return fast_info.market_cap
        
        print("❌ All methods failed to get market cap")
        return None
        
    except Exception as e:
        print(f"❌ Error getting MARA market cap: {e}")
        return None

def calculate_acmpe_ttm(quarters, market_cap, treasury_value, cash, total_debt):
    """Calculate ACMPE-TTM from quarterly data with policy enforcement and adjustments"""
    # Load adjustments if enabled
    adjustments = load_adjustments() if USE_ADJUSTMENTS else {}
    
    # Calculate core earnings for each quarter with policy enforcement
    quarters_core = []
    for q in quarters:
        # Enforce pre/post-ASU policy
        rv = apply_policy(q["period"], q["reval_used"])
        core_q = q["ni"] - rv + q["interest"]
        
        # Apply adjustments if any exist for this period
        period_adjustments = adjustments.get(q["period"], [])
        adj_sum = sum(a["impact"] for a in period_adjustments)
        core_adj = core_q + adj_sum
        
        # Expansion-only add-backs per quarter (future/growth/preop)
        fut_adj = sum(a["impact"] for a in period_adjustments if a.get("category") in {"future", "growth", "preop"})
        core_ops_only = core_q + fut_adj
        
        quarters_core.append({
            "period": q["period"],
            "ni": q["ni"],
            "reval_used": rv,  # Use policy-enforced value
            "interest": q["interest"],
            "core": core_q,
            "core_adj": core_adj,
            "core_ops_only": core_ops_only,
            "adjustments": period_adjustments,
            "adj_sum": adj_sum,
            "fut_adj_sum": fut_adj,
            "policy": "post-ASU" if q["period"] >= "2025-01-01" else "pre-ASU"
        })
    
    # Calculate Core TTM (unadjusted, adjusted, and ops-only)
    core_ttm = sum(q["core"] for q in quarters_core)
    core_ttm_adj = sum(q["core_adj"] for q in quarters_core)
    core_ttm_ops = sum(q["core_ops_only"] for q in quarters_core)
    
    # Calculate RBV (Residual Business Value)
    rbv = market_cap - (treasury_value + cash - total_debt)
    
    # Calculate ACMPE-TTM (all versions)
    acmpe_ttm = (rbv / core_ttm) if (rbv > 0 and core_ttm > 0) else None
    acmpe_ttm_adj = (rbv / core_ttm_adj) if (rbv > 0 and core_ttm_adj > 0) else None
    acmpe_ttm_ops = (rbv / core_ttm_ops) if (rbv > 0 and core_ttm_ops > 0) else None
    
    return quarters_core, core_ttm, core_ttm_adj, core_ttm_ops, rbv, acmpe_ttm, acmpe_ttm_adj, acmpe_ttm_ops

def calculate_prime_mnav(treasury_value, cash, debt, core_ttm, pe_scenarios=[5, 8, 11]):
    """
    Calculate PRIME mNAV (Peyton's Risk-Integrated Miner mNAV) using PE-based fair value
    Fair mNAV = 1.0 + (Cash - Debt) / Treasury + (PE × Core TTM) / Treasury
    
    This shows what mNAV should be if operations were valued at different PE multiples
    Returns dict with Bear (5x), Neutral (8x), and Bull (11x) scenarios
    
    Negative operations destroy value - that's the point! No floor.
    """
    prime_values = {}
    
    # Calculate cash-debt adjustment (always the same)
    cash_debt_adjustment = (cash - debt) / treasury_value
    
    for pe in pe_scenarios:
        if pe == 5:
            scenario = "Value PE (5×)"
        elif pe == 8:
            scenario = "Market PE (8×)" 
        elif pe == 11:
            scenario = "Growth PE (11×)"
        else:
            scenario = f"{pe}x"
        
        # PE × Core TTM = Business Value
        business_value = pe * core_ttm
        
        # Business Value ÷ Treasury Value = PE adjustment
        pe_adjustment = business_value / treasury_value
        
        # PRIME mNAV = 1.0 + cash-debt adjustment + PE adjustment
        prime_mnav = 1.0 + cash_debt_adjustment + pe_adjustment
        
        prime_values[scenario] = {
            'prime_mnav': prime_mnav,
            'cash_debt_adjustment': cash_debt_adjustment,
            'pe_adjustment': pe_adjustment,
            'business_value': business_value
        }
    
    return prime_values

def main():
    print("=== Simple MARA Valuation ===\n")
    
    # Show adjustment settings
    print(f"🔧 Adjustments: {'ON' if USE_ADJUSTMENTS else 'OFF'}")
    print(f"🔧 SBC Add-back: {'ON' if ADD_BACK_SBC else 'OFF'}")
    print()
    
    # Get basic data
    btc_price = get_btc_price()
    if not btc_price:
        print("❌ Failed to get BTC price")
        return
    
    mara_mc = get_mara_market_cap()
    if not mara_mc:
        print("❌ Failed to get MARA market cap")
        return
    
    # Get live cash and debt
    cash, total_debt = get_cash_and_debt()
    if cash is None or total_debt is None:
        print("❌ Failed to get live cash and debt data")
        return
    
    # Assume BTC holdings (you can update this)
    btc_holdings = 50639
    treasury = btc_holdings * btc_price
    
    # Calculate NAV and mNAV
    nav = treasury + cash - total_debt
    mnav = mara_mc / treasury
    
    print(f"💰 BTC Price: ${btc_price:,.0f}")
    print(f"📊 MARA Market Cap: ${mara_mc:,.0f}")
    print(f"🏦 Treasury (BTC × price): ${treasury:,.0f}")
    print(f"💵 Cash: ${cash:,.0f} (live from Yahoo Finance)")
    print(f"💳 Total Debt: ${total_debt:,.0f} (live from Yahoo Finance)")
    print(f"📈 NAV (treasury + cash - debt): ${nav:,.0f} (calculated with live data)")
    
    # Calculate ACMPE-TTM from quarterly data
    print(f"\n🔍 Calculating ACMPE-TTM from quarterly data...")
    quarters_core, core_ttm, core_ttm_adj, core_ttm_ops, rbv, acmpe_ttm, acmpe_ttm_adj, acmpe_ttm_ops = calculate_acmpe_ttm(MARA_QUARTERS, mara_mc, treasury, cash, total_debt)
    
    print(f"\n📊 Last 4 Quarters (Allworth Core Mining P/E Calculation)")
    print("   Pre-ASU: Only removes impairment losses (GAAP fair value accounting rules)")
    print("   Post-ASU: Removes full fair value changes (FASB ASU 2023-08 implementation)")
    print("   AdjustedCore adds back non-core items (see row notes).")
    print("   Period       NI           RevalUsed     Interest     Allworth Core Mining P/E Core (= NI - Reval + Int)   +Expansion   Allworth Core Mining P/E Core(Ops-Only)   Policy")
    print("   " + "-" * 150)
    
    for q in quarters_core:
        print(f"   {q['period']}  {q['ni']:>12,.0f}  {q['reval_used']:>12,.0f}  {q['interest']:>10,.0f}  {q['core']:>18,.0f}  {q['fut_adj_sum']:>10,.0f}  {q['core_ops_only']:>15,.0f}   {q['policy']}")
        
        # Show adjustments if any exist
        if q['adjustments']:
            for adj in q['adjustments']:
                impact_str = "+" if adj['impact'] > 0 else ""
                print(f"      {impact_str}{adj['impact']:,.0f} {adj['label']} ({adj['category']}: {adj['reason']})")
    
    # Add second table for clean operations view
    print(f"\n📊 Clean Operations View (Existing Sites Only)")
    print("   Removes: Expansion spending, debt-related items, financing noise")
    print("   Shows: What MARA would earn just running existing operations")
    print("   Period       Allworth Core Mining P/E Core        +Expansion   +Debt/Fin   Clean Ops   Policy")
    print("   " + "-" * 120)
    
    for q in quarters_core:
        # Calculate clean operations by adding back expansion and debt/financing items
        debt_fin_adj = sum(a["impact"] for a in q["adjustments"] if a.get("category") in {"financing", "debt"})
        clean_ops = q["core"] + q["fut_adj_sum"] + debt_fin_adj
        
        print(f"   {q['period']}  {q['core']:>12,.0f}  {q['fut_adj_sum']:>10,.0f}  {debt_fin_adj:>10,.0f}  {clean_ops:>10,.0f}   {q['policy']}")
        
        # Show what was added back for clean operations
        if q['fut_adj_sum'] != 0 or debt_fin_adj != 0:
            if q['fut_adj_sum'] != 0:
                print(f"      +{q['fut_adj_sum']:,.0f} expansion costs added back")
            if debt_fin_adj != 0:
                print(f"      +{debt_fin_adj:,.0f} debt/financing items added back")
    
    # Calculate clean operations TTM
    clean_ops_ttm = sum(q["core"] + q["fut_adj_sum"] + sum(a["impact"] for a in q["adjustments"] if a.get("category") in {"financing", "debt"}) for q in quarters_core)
    acmpe_clean_ops = (rbv / clean_ops_ttm) if (rbv > 0 and clean_ops_ttm > 0) else None
    
    print(f"\n📊 ACMPE-TTM Calculation:")
    # Determine which view to headline based on OPS_ONLY flag
    use_core = core_ttm_ops if OPS_ONLY else core_ttm
    use_acmpe = acmpe_ttm_ops if OPS_ONLY else acmpe_ttm
    use_label = "Ops-Only" if OPS_ONLY else "Unadjusted"
    
    print(f"   Allworth Core Mining P/E Core TTM ({use_label}): ${use_core:,.0f}")
    print(f"   Allworth Core Mining P/E Core TTM-Adj: ${core_ttm_adj:,.0f} (with non-core adjustments)")
    print(f"   Allworth Core Mining P/E Core TTM (Clean Ops): ${clean_ops_ttm:,.0f} (existing sites only)")
    print(f"   RBV: ${rbv:,.0f} (Market Cap - NAV = business value excluding BTC)")
    
    if use_acmpe:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM) ({use_label}): {use_acmpe:.1f}x (RBV ÷ Core TTM)")
    else:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM) ({use_label}): N/A (negative core or RBV)")
    
    if acmpe_ttm_adj:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM-Adj): {acmpe_ttm_adj:.1f}x (RBV ÷ Adjusted Core TTM)")
    else:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM-Adj): N/A (negative adjusted core or RBV)")
    
    if acmpe_clean_ops:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM Clean Ops): {acmpe_clean_ops:.1f}x (RBV ÷ Clean Operations TTM)")
    else:
        print(f"   Allworth Core Mining P/E (ACMPE-TTM Clean Ops): N/A (negative clean ops or RBV)")
    
    print(f"\n📊 Comparison Views:")
    print(f"   Allworth Core Mining P/E Core TTM (Unadjusted): ${core_ttm:,.0f} | Allworth Core Mining P/E Core TTM (Ops-Only): ${core_ttm_ops:,.0f} | Allworth Core Mining P/E Core TTM (Clean Ops): ${clean_ops_ttm:,.0f}")
    
    print(f"\n📝 Note: Decision gate uses {use_label} ACMPE-TTM. Adjusted multiple shown for context only.")
    print(f"📝 Policy Enforcement: Pre-ASU quarters enforce impairment-only removal; Post-ASU quarters apply full fair value accounting.")
    print(f"📝 Ops-Only view adds back expansion expenses (pre-operating, acquisition, commissioning) and leaves financing and BTC revaluation rules unchanged.")
    print(f"📝 Clean Operations view removes ALL non-operational items to show existing site performance only.")
    
    # Calculate PRIME mNAV
    prime_values = calculate_prime_mnav(treasury, cash, total_debt, clean_ops_ttm)
    
    print(f"\n📊 PRIME mNAV Scenarios (Peyton's Risk-Integrated Miner mNAV):")
    print("   📊 Business Value Floor: OFF (negative operations reduce fair value)")
    print(f"   🎯 Default PE: {FAIR_PE}x (set FAIR_PE env var to change)")
    
    for scenario, data in prime_values.items():
        print(f"   {scenario}: {data['prime_mnav']:.3f}x (Fair Value ÷ Treasury)")
    
    print(f"\n🧮 PRIME mNAV Calculation Breakdown:")
    cash_debt_adj = prime_values['Market PE (8×)']['cash_debt_adjustment']  # Same for all scenarios
    print(f"   Base: 1.0x")
    print(f"   Cash-Debt Adjustment: +{cash_debt_adj:+.3f}x (${cash:,.0f} - ${total_debt:,.0f}) ÷ ${treasury:,.0f}")
    balance_sheet_mnav = 1.0 + cash_debt_adj
    print(f"   Balance-sheet mNAV (neutral ops) = 1 + (Cash−Debt)/Treasury = {balance_sheet_mnav:.3f}×")
    print()
    
    for scenario, data in prime_values.items():
        if scenario == "Value PE (5×)":
            pe = 5
        elif scenario == "Market PE (8×)":
            pe = 8
        else:
            pe = 11
        
        print(f"   {scenario} ({pe}x PE): Core TTM ${core_ttm_ops:,.0f} × {pe}x = ${data['business_value']:,.0f} business value")
        print(f"           PE Adjustment: {data['pe_adjustment']:+.3f}x")
        print(f"           PRIME mNAV = 1.0 + {cash_debt_adj:+.3f} + {data['pe_adjustment']:+.3f} = {data['prime_mnav']:.3f}x")
        print()

    print(f"\n🎯 mNAV: {mnav:.2f}x (Market Cap ÷ Treasury)")
    
    print(f"\n🎯 Summary: mNAV: {mnav:.2f}x | PRIME mNAV: Value PE (5×) {prime_values['Value PE (5×)']['prime_mnav']:.3f}x | Market PE (8×) {prime_values['Market PE (8×)']['prime_mnav']:.3f}x | Growth PE (11×) {prime_values['Growth PE (11×)']['prime_mnav']:.3f}x | Allworth Core Mining P/E Core TTM (Clean Ops): ${clean_ops_ttm:,.0f}")
    
    # Add interpretation
    print(f"\n📊 PRIME mNAV Interpretation:")
    print(f"   Value PE (5x): Operations valued conservatively - Fair Value: {prime_values['Value PE (5×)']['prime_mnav']:.3f}x")
    print(f"   Market PE (8x): Operations valued at market average - Fair Value: {prime_values['Market PE (8×)']['prime_mnav']:.3f}x") 
    print(f"   Growth PE (11x): Operations valued optimistically - Fair Value: {prime_values['Growth PE (11×)']['prime_mnav']:.3f}x")
    
    if mnav < min(prime_values['Value PE (5×)']['prime_mnav'], prime_values['Market PE (8×)']['prime_mnav'], prime_values['Growth PE (11×)']['prime_mnav']):
        print(f"   🚀 Current mNAV ({mnav:.2f}x) < All PRIME mNAV scenarios - Potentially undervalued even in bear case")
    elif mnav > max(prime_values['Value PE (5×)']['prime_mnav'], prime_values['Market PE (8×)']['prime_mnav'], prime_values['Growth PE (11×)']['prime_mnav']):
        print(f"   ⚠️  Current mNAV ({mnav:.2f}x) > All PRIME mNAV scenarios - Potentially overvalued even in bull case")
    else:
        print(f"   ➖ Current mNAV ({mnav:.2f}x) falls within PRIME mNAV range - Reasonably valued")
    
    # Add TL;DR line
    print(f"\n🎯 TL;DR: PRIME mNAV (PE-adjusted): {prime_values['Value PE (5×)']['prime_mnav']:.3f}x / {prime_values['Market PE (8×)']['prime_mnav']:.3f}x / {prime_values['Growth PE (11×)']['prime_mnav']:.3f}x (5×/8×/11×). Current mNAV {mnav:.2f}x is {'above' if mnav > max(prime_values['Value PE (5×)']['prime_mnav'], prime_values['Market PE (8×)']['prime_mnav'], prime_values['Growth PE (11×)']['prime_mnav']) else 'below'} fair range ⇒ {'overvalued' if mnav > max(prime_values['Value PE (5×)']['prime_mnav'], prime_values['Market PE (8×)']['prime_mnav'], prime_values['Growth PE (11×)']['prime_mnav']) else 'undervalued'} on ops-PE basis.")

if __name__ == "__main__":
    main()
