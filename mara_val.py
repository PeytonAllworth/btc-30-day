import requests
import yfinance as yf
import json
import os
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional


def fmt_dollars(x: Optional[float]) -> str:
    return "Not found" if x is None else f"${x:,.0f}"


def fmt_float(x: Optional[float], decimals: int = 2) -> str:
    return "Not found" if x is None else f"{x:.{decimals}f}"


@dataclass
class DecisionCriteria:
    mnav_max_buy: float = 1.20       # mNAV below this → cheap vs treasury
    nav_discount_buy: float = 0.10   # NAV positive and premium/discount logic (optional)
    min_adj_ni: float = 0            # normalized NI must be >= this to avoid loss
    require_interest_and_reval: bool = False  # if True, we need both to compute normalized NI


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
        balance_sheet = mara.quarterly_balance_sheet
        
        if income_stmt is not None and not income_stmt.empty:
            latest_quarter = income_stmt.iloc[:, 0]  # First column is most recent quarter
            ts = income_stmt.columns[0]  # pandas Timestamp
            quarter_name = f"{ts.year}Q{ts.quarter}"
            
            # Get Net Income
            net_income = latest_quarter.get('Net Income', None)
            if net_income is None:
                net_income = latest_quarter.get('Net Income Common Stockholders', None)
            
            # Get Cash from balance sheet
            cash = None
            if balance_sheet is not None and not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]  # Most recent quarter
                cash = latest_balance.get('Cash And Cash Equivalents', None)
                if cash is None:
                    cash = latest_balance.get('Cash', None)
            
            if net_income is not None:
                return {
                    "quarter": quarter_name,
                    "reported_ni": net_income,
                    "cash": cash,
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

            # Debt: add a few common concepts and take the most recent quarterly for each
            debt_cur = us_gaap.get("DebtCurrent", {}).get("units", {}).get("USD", [])
            lt_debt = us_gaap.get("LongTermDebtNoncurrent", {}).get("units", {}).get("USD", [])
            lt_debt_leases = us_gaap.get("LongTermDebtAndCapitalLeaseObligations", {}).get("units", {}).get("USD", [])
            st_borrow = us_gaap.get("ShortTermBorrowings", {}).get("units", {}).get("USD", [])
            notes_cur = us_gaap.get("NotesPayableCurrent", {}).get("units", {}).get("USD", [])

            def pick(items, label):
                if items:
                    d = latest_quarterly(items)
                    val = d.get("val")
                    if val is not None:
                        results[label] = val

            pick(debt_cur, "debt_current")
            pick(lt_debt, "long_term_debt")
            pick(lt_debt_leases, "long_term_debt_and_capital_leases")
            pick(st_borrow, "short_term_borrowings")
            pick(notes_cur, "notes_payable_current")

            return results
            
        else:
            print(f"⚠️  SEC API returned status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching SEC data: {e}")
        return None

def get_total_debt():
    """
    Try Yahoo Finance first (quarterly balance sheet). 
    Fallback to SEC XBRL us-gaap concepts if needed.
    Returns a number (latest quarter) or None.
    """
    # 1) Yahoo
    try:
        mara = yf.Ticker("MARA")
        bs = mara.quarterly_balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]
            candidates = {
                "long_term": ["Long Term Debt", "LongTermDebt"],
                "short_term": ["Short Long Term Debt", "Current Debt", "Short Term Borrowings", "Debt Current"]
            }
            long_term = next((latest.get(k) for k in candidates["long_term"] if k in latest.index), 0)
            short_term = next((latest.get(k) for k in candidates["short_term"] if k in latest.index), 0)

            total = 0
            if long_term is not None: total += float(long_term)
            if short_term is not None: total += float(short_term)

            if total > 0:
                return total
    except Exception as e:
        print(f"⚠️ Yahoo debt fetch failed: {e}")

    # 2) SEC fallback
    try:
        data = fetch_sec_financials()  # you already call this; we'll extend it to return debt pieces
        if not data:
            return None

        debt_parts = []
        for key in ("debt_current", "long_term_debt", "long_term_debt_and_capital_leases"):
            if data.get(key) is not None:
                debt_parts.append(float(data[key]))

        if debt_parts:
            return sum(debt_parts)
    except Exception as e:
        print(f"⚠️ SEC debt fallback failed: {e}")

    return None


def evaluate_signals(metrics: Dict[str, Any], crit: DecisionCriteria) -> Dict[str, Any]:
    """
    Input metrics should include:
      - mnav (float)
      - nav_simple (float)
      - reported_ni (float or None)
      - btc_reval (float or None)
      - interest (float or None)
    Returns dict with 'signals' (list of reasons) and a 'score' + 'normalized_ni'
    """
    reasons: List[str] = []
    score = 0

    mnav = metrics.get("mnav")
    nav_simple = metrics.get("nav_simple")
    reported_ni = metrics.get("reported_ni")
    btc_reval = metrics.get("btc_reval")
    interest = metrics.get("interest")

    # 1) mNAV signal
    if mnav is not None:
        if mnav <= crit.mnav_max_buy:
            reasons.append(f"mNAV {mnav:.2f}x ≤ {crit.mnav_max_buy:.2f}x (trading near treasury value).")
            score += 1
        else:
            reasons.append(f"mNAV {mnav:.2f}x > {crit.mnav_max_buy:.2f}x (premium vs treasury).")
            score -= 1
    else:
        reasons.append("mNAV not available.")
    
    # 2) NAV sanity (positive NAV helps)
    if nav_simple is not None:
        if nav_simple > 0:
            reasons.append(f"NAV positive at {fmt_dollars(nav_simple)}.")
            score += 1
        else:
            reasons.append(f"NAV negative at {fmt_dollars(nav_simple)}.")
            score -= 1
    else:
        reasons.append("NAV not available.")

    # 3) Normalized NI (remove BTC reval; add back interest)
    normalized = None
    if reported_ni is not None:
        if btc_reval is not None:
            normalized = reported_ni - btc_reval
            if interest is not None:
                normalized_no_debt = normalized + interest
            else:
                normalized_no_debt = None

            if normalized is not None:
                if normalized >= crit.min_adj_ni:
                    reasons.append(f"Adj NI {fmt_dollars(normalized)} ≥ {fmt_dollars(crit.min_adj_ni)} (core earnings OK).")
                    score += 1
                else:
                    reasons.append(f"Adj NI {fmt_dollars(normalized)} < {fmt_dollars(crit.min_adj_ni)} (core earnings weak).")
                    score -= 1

            if normalized_no_debt is not None:
                reasons.append(f"Adj NI (no debt) {fmt_dollars(normalized_no_debt)} (interest burden isolated).")
        else:
            if crit.require_interest_and_reval:
                reasons.append("Missing BTC revaluation; cannot compute normalized earnings under strict mode.")
            else:
                reasons.append("Missing BTC revaluation; normalized NI partially unavailable.")
    else:
        reasons.append("Reported NI not available.")

    return {
        "reasons": reasons,
        "score": score,
        "normalized_ni": normalized
    }


def make_recommendation(result: Dict[str, Any]) -> Dict[str, str]:
    """
    Simple mapping from score → action. Tune later.
    """
    score = result["score"]
    if score >= 2:
        action = "BUY"
        summary = "Multiple value signals are positive; position sizing still your call."
    elif score <= -1:
        action = "HOLD/AVOID"
        summary = "Signals show premium or weak core earnings; wait for better setup."
    else:
        action = "NEUTRAL"
        summary = "Mixed signals; monitor and wait for clearer edge."
    return {"action": action, "summary": summary}


def build_report(metrics: Dict[str, Any], eval_out: Dict[str, Any], decision: Dict[str, str]) -> str:
    lines = []
    lines.append("=== MARA Miner Valuation — Explainer ===")
    lines.append("")
    lines.append("[1] Inputs (Today)")
    lines.append(f"   • BTC Price:         {fmt_dollars(metrics.get('btc_price'))}")
    lines.append(f"   • MARA Market Cap:   {fmt_dollars(metrics.get('market_cap'))}")
    lines.append(f"   • BTC Holdings:      50,639 BTC (assumed)")
    lines.append(f"   • Treasury Value:    {fmt_dollars(metrics.get('treasury_value'))}")
    lines.append(f"   • Cash:              {fmt_dollars(metrics.get('cash'))}")
    lines.append(f"   • Total Debt:        {fmt_dollars(metrics.get('total_debt'))}")
    lines.append("")
    lines.append("[2] Core Metrics")
    lines.append(f"   • NAV  = Treasury + Cash − Debt = {fmt_dollars(metrics.get('nav_simple'))}")
    mnav = metrics.get('mnav')
    lines.append(f"   • mNAV = Market Cap / Treasury   = {fmt_float(mnav)}x")
    lines.append("")
    lines.append("[3] Normalization (strip BTC volatility, isolate debt)")
    lines.append(f"   • Reported Net Income:           {fmt_dollars(metrics.get('reported_ni'))}")
    lines.append(f"   • BTC Revaluation (SEC):         {fmt_dollars(metrics.get('btc_reval'))}")
    lines.append(f"   • Interest Expense (SEC):        {fmt_dollars(metrics.get('interest'))}")
    lines.append(f"   • Adjusted NI (no reval):        {fmt_dollars(eval_out.get('normalized_ni'))}")
    # Optional: computed above inside evaluate_signals if you stored it; otherwise compute again safely.
    lines.append("")
    lines.append("[4] Signals — Step‑by‑Step Reasoning")
    for r in eval_out["reasons"]:
        lines.append(f"   • {r}")
    lines.append("")
    lines.append("[5] TL;DR")
    lines.append(f"   ACTION: {decision['action']} — {decision['summary']}")
    lines.append("")
    lines.append("Note: Educational tool. Not financial advice. Data may be delayed or incomplete.")
    return "\n".join(lines)


def send_email_report(body: str, subject: str, to_emails: List[str]) -> bool:
    """
    Uses SMTP with env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM", user)

    if not (host and user and pwd and from_addr):
        print("⚠️ Email not sent (missing SMTP env vars).")
        return False

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_emails)

        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(from_addr, to_emails, msg.as_string())
        print("📧 Email sent.")
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False


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

    # Get real cash data from financials
    financials = fetch_mara_financials()
    if financials and financials['cash'] is not None:
        cash = financials['cash']
        print(f"💵 Cash: ${cash:,.0f}")
    else:
        print("💵 Cash: Not found")
        cash = 0  # Use 0 for NAV calculation if not found
    
    total_debt = get_total_debt()
    if total_debt is None:
        print("💳 Total Debt: Not found (using $0)")
        total_debt = 0
    else:
        print(f"💳 Total Debt: ${total_debt:,.0f}")
    nav_simple = treasury_value + cash - total_debt
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
    
    # Collect metrics for decision/report
    metrics = {
        "btc_price": btc_price,
        "market_cap": market_cap,
        "treasury_value": treasury_value,
        "cash": cash,
        "total_debt": total_debt,
        "nav_simple": nav_simple,
        "mnav": mnav,
        "reported_ni": None,
        "btc_reval": None,
        "interest": None
    }

    # Fill in normalized pieces from your existing fetches
    if financials:
        metrics["reported_ni"] = financials.get("reported_ni")

    if sec_data:
        metrics["btc_reval"] = sec_data.get("btc_reval")
        metrics["interest"] = sec_data.get("interest")

    # Evaluate & decide
    crit = DecisionCriteria()
    eval_out = evaluate_signals(metrics, crit)
    decision = make_recommendation(eval_out)

    # Build and print the explainer + TL;DR
    report = build_report(metrics, eval_out, decision)
    print("\n" + "="*60)
    print(report)

    # Optional: email if user configured recipients
    recipients_env = os.getenv("ALERT_RECIPIENTS", "")
    recipients = [e.strip() for e in recipients_env.split(",") if e.strip()]
    if recipients:
        subject = f"MARA Signal — {decision['action']}"
        send_email_report(report, subject, recipients)
    
    print("\n[C] Forward Projection — TODO")
    print("[D] Valuation — TODO")
    print("Action — TODO")

if __name__ == "__main__":
    main()
