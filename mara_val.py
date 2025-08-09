import requests
import yfinance as yf
import json


def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": "bitcoin", "vs_currencies": "usd"}, timeout=5)
        r.raise_for_status()
        return r.json()["bitcoin"]["usd"]
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        return float(input("Enter BTC price manually: "))

def get_mara_market_cap():
    try:
        mara = yf.Ticker("MARA")
        mc = mara.info.get("marketCap")
        if mc:
            return mc
        else:
            raise ValueError("Market cap not found")
    except Exception as e:
        print(f"Error fetching MARA market cap: {e}")
        return float(input("Enter MARA market cap manually: "))

def fetch_mara_financials():
    """Fetch real MARA quarterly financial data"""
    try:
        mara = yf.Ticker("MARA")
        
        # Get quarterly income statement (replaces deprecated earnings)
        income_stmt = mara.quarterly_income_stmt
        if income_stmt is not None and not income_stmt.empty:
            latest_quarter = income_stmt.iloc[:, 0]  # First column is most recent quarter
            ts = income_stmt.columns[0]  # pandas Timestamp
            quarter_name = f"{ts.year}Q{ts.quarter}"
            
            # Get Net Income
            net_income = latest_quarter.get('Net Income', None)
            if net_income is None:
                net_income = latest_quarter.get('Net Income Common Stockholders', None)
            
            if net_income is not None:
                return {
                    "quarter": quarter_name,
                    "reported_ni": net_income,
                    "btc_reval": None,  # Need to find BTC revaluation data
                    "interest": None    # Need to find interest expense data
                }
            else:
                print("⚠️  Net Income not found in income statement")
                return None
        else:
            print("⚠️  Could not fetch income statement data")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching MARA financials: {e}")
        return None

def get_cik_from_ticker(ticker):
    """Get 10-digit CIK from SEC company_tickers.json"""
    try:
        import os
        cache_file = "company_tickers.json"

        if not os.path.exists(cache_file):
            print("📥 Downloading SEC company_tickers.json …")
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {'User-Agent': 'MARA-Valuation-Tool/1.0 (educational-use@example.com)'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            with open(cache_file, "w") as f:
                f.write(resp.text)
            print("✅ Cached company tickers")

        with open(cache_file, "r") as f:
            tickers = json.load(f)  # dict: "0": {"ticker": "...", "cik_str": 1234567, ...}, ...

        t = ticker.upper()
        for _, company in tickers.items():
            if company.get("ticker") == t:
                cik10 = str(company.get("cik_str")).zfill(10)
                return cik10

        print(f"⚠️ Ticker {ticker} not found in SEC database")
        return None

    except Exception as e:
        print(f"❌ Error getting CIK: {e}")
        return None

def fetch_sec_financials():
    """Fetch MARA financial data from SEC filings using proper API strategy"""
    try:
        print("🔍 Fetching SEC filing data...")
        
        # helper function to get most recent entry by end date
        def latest_by_end(items):
            return max(items, key=lambda x: x.get("end", ""))
        
        # helper function to get most recent quarterly entry
        def latest_quarterly(items):
            # Prefer quarterly points: fp in Q1..Q4 OR qtrs == 1 OR duration 'P3M'
            quarterly = [
                x for x in items
                if x.get("fp") in {"Q1","Q2","Q3","Q4"} or x.get("qtrs") == 1 or x.get("dur") == "P3M"
            ]
            pool = quarterly or items  # fallback if none tagged
            return max(pool, key=lambda x: x.get("end", ""))
        
        # Step 1: Get CIK from ticker
        cik = get_cik_from_ticker("MARA")
        if not cik:
            print("❌ Could not resolve MARA CIK")
            return None
        
        print(f"   Found CIK: {cik}")
        
        # Step 2: Rate limiting
        import time
        time.sleep(0.1)  # 10 requests per second max
        
        # Step 3: Get company facts (XBRL data)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {
            'User-Agent': 'MARA-Valuation-Tool/1.0 (educational-use@example.com)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   SEC API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            us_gaap = data.get("facts", {}).get("us-gaap", {})
            results = {}

            # Net Income
            ni_units = us_gaap.get("NetIncomeLoss", {}).get("units", {}).get("USD", [])
            if ni_units:
                latest_ni = latest_quarterly(ni_units)
                results["net_income"] = latest_ni.get("val")
                results["ni_period"] = latest_ni.get("end")
                print(f"   Found Quarterly Net Income: ${results['net_income']:,.0f} ({results['ni_period']})")

            # Interest Expense
            int_units = us_gaap.get("InterestExpense", {}).get("units", {}).get("USD", [])
            if int_units:
                latest_interest = latest_quarterly(int_units)
                results["interest"] = latest_interest.get("val")
                print(f"   Found Quarterly Interest: ${results['interest']:,.0f}")

            # Try a few generic investment reval concepts (may/may not exist for BTC)
            for concept in ("NetRealizedAndUnrealizedGainLossOnInvestments",
                            "UnrealizedGainLossOnInvestments",
                            "RealizedGainLossOnInvestments"):
                units = us_gaap.get(concept, {}).get("units", {}).get("USD", [])
                if units:
                    latest_btc = latest_quarterly(units)
                    results["btc_reval"] = latest_btc.get("val")
                    print(f"   Found investment reval (quarterly): ${results['btc_reval']:,.0f}")
                    break

            return results
            
        else:
            print(f"⚠️  SEC API returned status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching SEC data: {e}")
        return None

def main():
    print("=== MARA Miner Valuation Tool (Quick-Start) ===")
    print()
    
    btc_price = get_btc_price()
    market_cap = get_mara_market_cap()
    print()

    print(f"💰 BTC Price: ${btc_price:,.0f}")
    print(f"📊 MARA Market Cap: ${market_cap:,.0f}")
    print()

    btc_units = 50639
    treasury_value = btc_units * btc_price
    print(f"🏦 Treasury (BTC holdings x price): ${treasury_value:,.0f}")
    print()

    cash = 100_000_000
    total_debt = 2_630_000_000
    nav_simple = treasury_value + cash - total_debt
    print(f"💵 Cash: ${cash:,.0f}")
    print(f"💳 Total Debt: ${total_debt:,.0f}")
    print(f"📈 NAV (treasury + cash - debt): ${nav_simple:,.0f}")
    print()

    mnav = market_cap / treasury_value
    print(f"🎯 mNAV (Market Cap / Treasury): {mnav:.2f}x")
    print()

    # Fetch real financial data
    print("[B] Normalized History")
    financials = fetch_mara_financials()
    sec_data = fetch_sec_financials()
    
    if financials and sec_data:
        print(f"📊 {financials['quarter']} | Reported NI: ${financials['reported_ni']:,.0f}")
        
        # Use SEC data for normalization
        btc_reval = sec_data.get('btc_reval')
        interest = sec_data.get('interest')
        sec_ni = sec_data.get('net_income')
        
        # Show SEC Net Income if different from Yahoo Finance
        if sec_ni and abs(sec_ni - financials['reported_ni']) > 1000:
            print(f"   SEC Net Income: ${sec_ni:,.0f} (diff: ${sec_ni - financials['reported_ni']:,.0f})")
        
        if btc_reval is not None:
            adj_ni = financials['reported_ni'] - btc_reval
            print(f"   BTC Reval: ${btc_reval:,.0f} | Adj NI: ${adj_ni:,.0f}")
        else:
            print("   ⚠️  BTC revaluation data not available from SEC")
        
        if interest is not None:
            adj_ni_no_debt = adj_ni + interest
            print(f"   Interest: ${interest:,.0f} | Adj NI (no debt): ${adj_ni_no_debt:,.0f}")
        else:
            print("   ⚠️  Interest expense data not available from SEC")
    elif financials:
        print(f"📊 {financials['quarter']} | Reported NI: ${financials['reported_ni']:,.0f}")
        print("   ⚠️  SEC data unavailable - cannot normalize")
    else:
        print("❌ Could not fetch financial data")
    
    print("\n[C] Forward Projection — TODO")
    print("[D] Valuation — TODO")
    print("Action — TODO")

if __name__ == "__main__":
    main()
