#!/usr/bin/env python3
"""
Simple MARA Valuation Tool
Just mNAV and ACMPE-TTM. That's it.
"""

import requests
import yfinance as yf
import json
import os

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
        mara = yf.Ticker("MARA")
        return mara.info["marketCap"]
    except:
        return None

def calculate_acmpe_ttm(quarters, market_cap, treasury_value, cash=109_475_000, total_debt=2_600_546_000):
    """Calculate ACMPE-TTM from quarterly data"""
    # Calculate core earnings for each quarter
    quarters_core = []
    for q in quarters:
        core_q = q["ni"] - q["reval_used"] + q["interest"]
        quarters_core.append({
            "period": q["period"],
            "ni": q["ni"],
            "reval_used": q["reval_used"],
            "interest": q["interest"],
            "core": core_q,
            "policy": q["policy"]
        })
    
    # Calculate Core TTM
    core_ttm = sum(q["core"] for q in quarters_core)
    
    # Calculate RBV (Residual Business Value)
    rbv = market_cap - (treasury_value + cash - total_debt)
    
    # Calculate ACMPE-TTM
    acmpe_ttm = (rbv / core_ttm) if (rbv > 0 and core_ttm > 0) else None
    
    return quarters_core, core_ttm, rbv, acmpe_ttm

def main():
    print("=== Simple MARA Valuation ===\n")
    
    # Get basic data
    btc_price = get_btc_price()
    if not btc_price:
        print("❌ Failed to get BTC price")
        return
    
    mara_mc = get_mara_market_cap()
    if not mara_mc:
        print("❌ Failed to get MARA market cap")
        return
    
    # Assume BTC holdings (you can update this)
    btc_holdings = 50639
    treasury = btc_holdings * btc_price
    
    # Calculate mNAV
    mnav = mara_mc / treasury
    
    print(f"💰 BTC Price: ${btc_price:,.0f}")
    print(f"📊 MARA Market Cap: ${mara_mc:,.0f}")
    print(f"🏦 Treasury (BTC × price): ${treasury:,.0f}")
    print(f"🎯 mNAV: {mnav:.2f}x")
    
    # Calculate ACMPE-TTM from quarterly data
    print(f"\n🔍 Calculating ACMPE-TTM from quarterly data...")
    quarters_core, core_ttm, rbv, acmpe_ttm = calculate_acmpe_ttm(MARA_QUARTERS, mara_mc, treasury)
    
    print(f"\n📊 Last 4 Quarters (Core Earnings Calculation)")
    print("   Period       NI           RevalUsed     Interest     Core (= NI - Reval + Int)   Policy")
    print("   " + "-" * 90)
    
    for q in quarters_core:
        print(f"   {q['period']}  {q['ni']:>12,.0f}  {q['reval_used']:>12,.0f}  {q['interest']:>10,.0f}  {q['core']:>18,.0f}   {q['policy']}")
    
    print(f"\n📊 ACMPE-TTM Calculation:")
    print(f"   Core TTM: ${core_ttm:,.0f}")
    print(f"   RBV: ${rbv:,.0f}")
    if acmpe_ttm:
        print(f"   ACMPE-TTM: {acmpe_ttm:.1f}x")
    else:
        print(f"   ACMPE-TTM: N/A (negative core or RBV)")
    
    print(f"\n🎯 Summary: mNAV: {mnav:.2f}x | Core TTM: ${core_ttm:,.0f}")

if __name__ == "__main__":
    main()
