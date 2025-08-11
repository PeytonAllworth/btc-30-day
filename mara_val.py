import requests
import yfinance as yf
import json
import os
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional


# === Metric labels ===
METRIC_NAME = "Allworth Core Mining P/E"
METRIC_SHORT = "ACMPE"

# === Feature flags ===
SHOW_FORWARD = os.getenv("SHOW_FORWARD", "0") == "1"


def fmt_dollars(x: Optional[float]) -> str:
    return "Not found" if x is None else f"${x:,.0f}"


def fmt_float(x: Optional[float], decimals: int = 2) -> str:
    return "Not found" if x is None else f"{x:.{decimals}f}"


def fmt_mult(x: float | None) -> str:
    return "N/A" if (x is None) else f"{x:.1f}x"


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
                results["interest_period"] = latest_interest.get("end")
                print(f"   Found Quarterly Interest: ${results['interest']:,.0f}")

            # Use strict P&L reval filtering (no balance sheet levels)
            strict_reval = sec_reval_series_strict(12)
            if strict_reval:
                # Find reval for the same period as Net Income
                ni_end = results.get("ni_period")
                if ni_end and ni_end in strict_reval:
                    reval_data = strict_reval[ni_end]
                    results["btc_reval"] = reval_data["val"]
                    results["btc_reval_concept"] = reval_data["src"]
                    results["btc_reval_period"] = ni_end
                    print(f"   Found P&L reval: ${results['btc_reval']:,.0f} ({results['btc_reval_concept']}) [{ni_end}]")
                else:
                    print(f"   ⚠️  No P&L reval found for NI period {ni_end}")
                    results["btc_reval"] = None
                    results["btc_reval_period"] = None
            else:
                print(f"   ⚠️  No P&L reval concepts found")
                results["btc_reval"] = None
                results["btc_reval_period"] = None

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
      - acmpe_ttm (float or None)
      - rbv (float or None)
    Returns dict with 'signals' (list of reasons) and a 'score' + 'normalized_ni'
    """
    reasons: List[str] = []
    score = 0

    mnav = metrics.get("mnav")
    nav_simple = metrics.get("nav_simple")
    reported_ni = metrics.get("reported_ni")
    btc_reval = metrics.get("btc_reval")
    interest = metrics.get("interest")
    acmpe_ttm = metrics.get("acmpe_ttm")
    rbv = metrics.get("rbv")

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

    # 4) ACMPE-TTM signal (new mining P/E metric)
    if acmpe_ttm is not None and rbv is not None:
        if rbv > 0:
            if acmpe_ttm <= 20:  # Conservative threshold
                reasons.append(f"ACMPE-TTM {acmpe_ttm:.1f}x ≤ 20x (mining operations reasonably priced).")
                score += 1
            else:
                reasons.append(f"ACMPE-TTM {acmpe_ttm:.1f}x > 20x (mining operations expensive).")
                score -= 1
        else:
            reasons.append(f"RBV {fmt_dollars(rbv)} ≤ 0 (market prices at/under asset value).")
            score -= 1
    else:
        reasons.append("ACMPE-TTM not available (insufficient aligned data).")

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


def build_report(metrics: Dict[str, Any], eval_out: Dict[str, Any], decision: Dict[str, str], sec_data: Optional[Dict[str, Any]] = None, proj_rows: Optional[List[Dict[str, Any]]] = None) -> str:
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
    lines.append(f"   • mNAV = Market Cap / Treasury   = {fmt_mult(mnav)}")
    
    # Add ACMPE-TTM
    acmpe = metrics.get('acmpe_ttm')
    rbv = metrics.get('rbv')
    core_ttm = metrics.get('core_ttm')
    
    if acmpe is not None:
        lines.append(f"   • ACMPE-TTM = RBV ÷ Core TTM = {fmt_mult(acmpe)}")
        lines.append(f"   • RBV (Residual Business Value) = {fmt_dollars(rbv)}")
        lines.append(f"   • Core TTM (4 quarters) = {fmt_dollars(core_ttm)}")
    else:
        lines.append("   • ACMPE-TTM = N/A (insufficient data or RBV ≤ 0)")
    
    # Add ACMPE-RunRate if available
    acmpe_runrate = metrics.get('acmpe_runrate')
    if acmpe_runrate is not None:
        lines.append(f"   • ACMPE-RunRate (last qtr ×4) = {fmt_mult(acmpe_runrate)}")
    
    # Add ACMPE-FWD (only if enabled and credible)
    acmpe_fwd = metrics.get('acmpe_fwd')
    if acmpe_fwd is not None:
        lines.append(f"   • ACMPE-FWD (Base) = RBV ÷ Core_q = {fmt_mult(acmpe_fwd)}")
    elif SHOW_FORWARD:
        lines.append("   • ACMPE-FWD (Base) = N/A (inputs not credible)")
    else:
        lines.append("   • ACMPE-FWD (Base) = Disabled (set SHOW_FORWARD=1)")
    
    lines.append("")
    lines.append("[3] Normalization (strip BTC volatility, isolate debt)")
    ni_p = sec_data.get('ni_period') if sec_data else None
    rev_p = sec_data.get('btc_reval_period') if sec_data else None
    int_p = sec_data.get('interest_period') if sec_data else None
    
    lines.append(f"   • Reported Net Income [SEC]: {fmt_dollars(metrics.get('reported_ni'))}" + (f" [{ni_p}]" if ni_p else ""))
    br = metrics.get('btc_reval')
    br_tag = sec_data.get('btc_reval_concept') if sec_data else None
    lines.append(f"   • BTC Revaluation (SEC):     {fmt_dollars(br)}" + (f" [{br_tag}]" if br_tag else "") + (f" [{rev_p}]" if rev_p else ""))
    lines.append(f"   • Interest Expense (SEC):    {fmt_dollars(metrics.get('interest'))}" + (f" [{int_p}]" if int_p else ""))
    
    if metrics["adj_ni"] is not None:
        lines.append(f"   • Adjusted NI: {fmt_dollars(metrics['adj_ni'])}")
        lines.append(f"   • Adjusted NI (no debt): {fmt_dollars(metrics['adj_ni_no_debt'])}")
    else:
        lines.append("   • Adjusted NI: Skipped — different quarters.")
    
    # Add quarterly history table
    lines.append("")
    lines.append("[3b] Last 4 Quarters (SEC-only, aligned)")
    quarterly_rows = build_quarterly_history()
    if quarterly_rows:
        lines.append("   Period      ReportedNI   Reval    Interest   AdjNI   AdjNI(no debt)")
        lines.append("   " + "-" * 70)
        for row in quarterly_rows:
            period = row["period"][:10] if row["period"] else "Unknown"
            lines.append(f"   {period:<12} {fmt_dollars(row['reported_ni']):<11} {fmt_dollars(row['reval']):<8} {fmt_dollars(row['interest']):<9} {fmt_dollars(row['adj_ni']):<7} {fmt_dollars(row['adj_ni_no_debt'])}")
    else:
        lines.append("   ⚠️  Could not build quarterly history (missing data)")
    
    # Add forward projection table
    lines.append("")
    lines.append("[3c] Forward Projection (Constant BTC)")
    lines.append("   " + "-" * 80)
    
    if proj_rows:
        lines.append("   Scenario   BTC Mined   Revenue        Power Cost     Core_q        ACMPE-FWD")
        lines.append("   " + "-" * 80)
        for r in proj_rows:
            lines.append(f"   {r['name']:<9}  {r['btc_mined']:.2f}      {fmt_dollars(r['revenue']):>12}  {fmt_dollars(r['power_cost']):>12}  {fmt_dollars(r['core_q']):>12}  {fmt_mult(r['acmpe_fwd']):>9}")
    elif SHOW_FORWARD:
        lines.append("   Disabled (inputs not credible - check parameters)")
    else:
        lines.append("   Disabled (set SHOW_FORWARD=1 and provide real inputs)")
    
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
        print("   Example configuration:")
        print("   export SMTP_HOST='smtp.office365.com'")
        print("   export SMTP_PORT='587'")
        print("   export SMTP_USER='you@example.com'")
        print("   export SMTP_PASS='app_password'")
        print("   export SMTP_FROM='you@example.com'")
        print("   export ALERT_RECIPIENTS='friend1@example.com,friend2@example.com'")
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


def should_send_email(action: str, period: str) -> bool:
    """
    Check if we should send email based on state changes.
    Only send when action or period changes.
    """
    state_file = ".mara_last.json"
    
    try:
        # Read current state
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                last_state = json.load(f)
        else:
            last_state = {"action": None, "period": None}
        
        # Check if anything changed
        changed = (last_state.get("action") != action or 
                  last_state.get("period") != period)
        
        if changed:
            # Update state
            new_state = {"action": action, "period": period}
            with open(state_file, "w") as f:
                json.dump(new_state, f)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"⚠️ State check failed: {e}")
        return True  # Default to sending if state check fails


def project_core_q(p: dict) -> dict:
    """
    Projects next-quarter 'core' earnings at constant BTC (reval = 0).
    Inputs:
      p = {
        "mara_eh": float,                 # MARA hashrate, exahash/second
        "network_eh": float,              # Network hashrate, exahash/second
        "btc_price": float,               # live BTC price
        "fee_pct_of_subsidy": float,      # e.g., 0.10 means fees ≈ 10% of subsidy
        "efficiency_j_per_th": float,     # fleet efficiency, Joules per TH
        "power_cost_per_mwh": float,      # $ per MWh
        "other_opex_per_q": float,        # non-power opex per quarter ($)
        "depr_per_q": float,              # depreciation per quarter ($)
        "interest_per_q": float           # interest per quarter ($) [added back in core]
      }
    Returns: dict with btc_mined, revenue, power_cost, ebit, core_q
    """
    # Blocks per quarter (~90 days)
    blocks_q = 144 * 90
    # Block reward (post-halving) including fee uplift as % of subsidy
    subsidy_btc = 3.125
    reward_btc = subsidy_btc * (1 + float(p["fee_pct_of_subsidy"]))

    # Share of network
    share = float(p["mara_eh"]) / float(p["network_eh"])
    btc_mined = share * blocks_q * reward_btc
    revenue = btc_mined * float(p["btc_price"])

    # Power cost:
    # Convert EH/s -> TH/s, then TH/s * (J/TH) = Watts
    THs = float(p["mara_eh"]) * 1e6
    power_W = THs * float(p["efficiency_j_per_th"])
    seconds_q = 90 * 24 * 3600
    # Watt-seconds -> Wh (/3600), then -> MWh (/1e6)
    mwh = power_W * seconds_q / 3.6e9
    power_cost = mwh * float(p["power_cost_per_mwh"])

    # EBIT ~ revenue - power - opex - depreciation
    ebit = revenue - power_cost - float(p["other_opex_per_q"]) - float(p["depr_per_q"])

    # Core_q at constant BTC: NI - reval + interest ≈ EBIT (ignoring taxes)
    core_q = ebit  # reval=0 by assumption; add-back of interest nets out if you tax later

    return {
        "btc_mined": btc_mined,
        "revenue": revenue,
        "power_cost": power_cost,
        "ebit": ebit,
        "core_q": core_q,
        "interest": float(p["interest_per_q"])
    }


def compute_acmpe_fwd(market_cap: float, treasury_value: float, cash: float, total_debt: float, core_q: float) -> float | None:
    """
    ACMPE-FWD = RBV / Core_q, where RBV = MarketCap - (Treasury + Cash - Debt).
    Returns None if RBV <= 0 or Core_q <= 0.
    """
    try:
        rbv = float(market_cap) - (float(treasury_value) + float(cash) - float(total_debt))
        if rbv <= 0 or core_q is None or core_q <= 0:
            return None
        return rbv / core_q
    except Exception:
        return None


def params_quality_ok(p: dict) -> bool:
    """Check if forward projection parameters are credible"""
    try:
        return (
            p["mara_eh"] > 0 and p["network_eh"] > 0 and
            5 <= p["efficiency_j_per_th"] <= 40 and
            20 <= p["power_cost_per_mwh"] <= 200 and
            p["other_opex_per_q"] >= 0 and p["depr_per_q"] >= 0
        )
    except Exception:
        return False


# === Strict reval filtering (P&L only, post-ASU 2023-08) ===
REVAL_INCLUDE = ("gain", "loss", "gainloss", "changeinfairvalue", "fairvaluechange")
REVAL_ASSET = ("digital", "crypto", "cryptocurrency", "bitcoin", "btc")
REVAL_EXCLUDE = ("cost", "current", "noncurrent", "purchase", "mining")  # NOTE: removed "fairvalue"

def looks_like_reval_pnl(concept_name: str) -> bool:
    """Check if concept looks like P&L revaluation, not balance sheet levels"""
    n = concept_name.lower().replace("_", "")
    has_signal = any(k in n for k in REVAL_INCLUDE) or ("fairvalue" in n and "change" in n)
    return has_signal and any(k in n for k in REVAL_ASSET) and not any(k in n for k in REVAL_EXCLUDE)

def sec_reval_series_strict(n: int = 12) -> dict:
    """Return {end: {'val': float, 'filed': str, 'src': 'prefix:Concept'}} for P&L-style digital-asset reval only."""
    out = {}
    try:
        cik = get_cik_from_ticker("MARA")
        if not cik: return out
        import time, requests
        time.sleep(0.1)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {'User-Agent': 'MARA-Valuation-Tool/1.0 (educational-use@example.com)'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        facts = r.json().get("facts") or {}
        for tax, concepts in facts.items():
            for concept, payload in concepts.items():
                if not looks_like_reval_pnl(concept):
                    continue
                usd = (payload.get("units") or {}).get("USD", [])
                q = [x for x in usd if (x.get("fp") in {"Q1","Q2","Q3","Q4"} or x.get("qtrs")==1 or x.get("dur")=="P3M")]
                for x in q:
                    end, val, filed = x.get("end"), x.get("val"), x.get("filed")
                    if end and val is not None:
                        prev = out.get(end)
                        if (prev is None) or (filed and prev["filed"] < filed):
                            out[end] = {"val": float(val), "filed": filed or "", "src": f"{tax}:{concept}"}
        # keep only post-ASU periods (fiscal years beginning 2025+)
        post_asu_ends = [k for k in out.keys() if post_asu(k)]
        if post_asu_ends:
            # keep recent n post-ASU periods
            ends = sorted(post_asu_ends)[-n:]
            return {k: out[k] for k in ends}
        else:
            return {}  # no post-ASU periods found
    except Exception as e:
        print(f"⚠️ reval strict scan failed: {e}")
        return out


def post_asu(end_date: str) -> bool:
    """Check if period is post-ASU 2023-08 (fiscal years beginning 2025+)"""
    return end_date >= "2025-01-01"  # adjust if MARA early-adopted


def fetch_sec_latest_custom_reval(n: int = 1):
    """
    Scan ALL taxonomies (not just us-gaap) for concepts that look like digital-asset revaluation.
    Returns a list of {end, val, concept} sorted by end date (most recent first).
    """
    try:
        cik = get_cik_from_ticker("MARA")
        if not cik: return []
        import time, requests
        time.sleep(0.1)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {'User-Agent': 'MARA-Valuation-Tool/1.0 (educational-use@example.com)'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        facts = data.get("facts", {}) or {}

        # Enhanced search keys for digital/crypto/bitcoin
        KEYS = ("digitalasset", "digitalassets", "crypto", "cryptocurrency", "bitcoin", "btc")
        
        # search keys for digital/crypto/bitcoin
        hits = []
        for taxonomy, concepts in facts.items():
            if taxonomy.lower() == "dei":
                continue
            for concept, payload in concepts.items():
                # Clean concept name for better matching
                name = concept.lower().replace("_", "")
                if any(k in name for k in KEYS):
                    usd = (payload.get("units") or {}).get("USD", [])
                    # quarterly-ish filter
                    q = [x for x in usd if (x.get("fp") in {"Q1","Q2","Q3","Q4"} or x.get("qtrs")==1 or x.get("dur")=="P3M")]
                    for x in q:
                        val = x.get("val")
                        end = x.get("end")
                        if val is not None and end:
                            hits.append({"end": end, "val": val, "concept": f"{taxonomy}:{concept}"})
                            print(f"     Found reval: {taxonomy}:{concept} = ${val:,.0f} ({end})")
        
        # After building hits, prefer ends that exist in NI for alignment
        if hits:
            try:
                ni_series = fetch_sec_quarterly_values("NetIncomeLoss", 12)
                ni_ends = set(item.get("end") for item in ni_series if item.get("end"))
                # Filter to prefer NI-aligned periods, but fallback to all if none match
                aligned_hits = [h for h in hits if h["end"] in ni_ends]
                if aligned_hits:
                    hits = aligned_hits
                    print(f"   Found {len(hits)} NI-aligned reval concepts")
                else:
                    print(f"   Found {len(hits)} reval concepts (none aligned with NI)")
                    # Force recent data by filtering out ancient entries
                    recent_cutoff = "2023-01-01"
                    recent_hits = [h for h in hits if h["end"] >= recent_cutoff]
                    if recent_hits:
                        hits = recent_hits
                        print(f"   Filtered to {len(hits)} recent concepts (since {recent_cutoff})")
                    else:
                        print(f"   ⚠️  All reval concepts are ancient (before {recent_cutoff})")
            except Exception as e:
                print(f"   ⚠️  Could not check NI alignment: {e}")
        
        hits.sort(key=lambda z: z["end"], reverse=True)
        return hits[:n]
    except Exception as e:
        print(f"⚠️ SEC custom reval scan failed: {e}")
        return []


def fetch_sec_quarterly_values(concept: str, n: int = 8) -> List[Dict[str, Any]]:
    """
    Fetch the last n quarterly values for a given SEC concept.
    Returns list of {end, val} dicts sorted by end date (most recent first).
    """
    try:
        cik = get_cik_from_ticker("MARA")
        if not cik: return []
        
        import time
        time.sleep(0.1)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {'User-Agent': 'MARA-Valuation-Tool/1.0 (educational-use@example.com)'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        us_gaap = data.get("facts", {}).get("us-gaap", {})
        concept_data = us_gaap.get(concept, {})
        usd_units = concept_data.get("units", {}).get("USD", [])
        
        if not usd_units:
            return []
        
        # Filter for quarterly data
        quarterly = [
            x for x in usd_units
            if x.get("fp") in {"Q1","Q2","Q3","Q4"} or x.get("qtrs") == 1 or x.get("dur") == "P3M"
        ]
        
        # Sort by end date and take most recent n
        quarterly.sort(key=lambda x: x.get("end", ""), reverse=True)
        return [{"end": x.get("end"), "val": x.get("val")} for x in quarterly[:n]]
        
    except Exception as e:
        print(f"⚠️ SEC quarterly fetch failed for {concept}: {e}")
        return []


def build_quarterly_history() -> List[Dict[str, Any]]:
    """
    Build a 4-quarter normalized history table from SEC data.
    Returns list of dicts with aligned periods.
    """
    # Fetch quarterly data for each concept
    ni = fetch_sec_quarterly_values("NetIncomeLoss", n=8)
    ie = fetch_sec_quarterly_values("InterestExpense", n=8)
    
    # Try different reval concepts
    reval = None
    for concept in ("NetRealizedAndUnrealizedGainLossOnInvestments", 
                   "UnrealizedGainLossOnInvestments", 
                   "RealizedGainLossOnInvestments"):
        reval = fetch_sec_quarterly_values(concept, n=8)
        if reval:
            break
    
    # If no standard reval, try custom digital asset concepts
    if not reval:
        custom = fetch_sec_latest_custom_reval(8)
        reval = [{"end": x["end"], "val": x["val"]} for x in custom]
    
    if not (ni and ie and reval):
        return []
    
    # Index by end date for easy lookup
    def index_by_end(xs):
        return {x["end"]: x["val"] for x in xs if x.get("end") and x.get("val") is not None}
    
    i_ni = index_by_end(ni)
    i_ie = index_by_end(ie)
    i_rev = index_by_end(reval)
    
    # Find common periods
    common_periods = sorted(set(i_ni.keys()) & set(i_ie.keys()) & set(i_rev.keys()))[-4:]
    
    # Build rows
    rows = []
    for end in common_periods:
        rni = i_ni[end]
        rev = i_rev[end]
        inx = i_ie[end]
        adj = rni - rev
        adj_no_debt = adj + inx
        
        rows.append({
            "period": end,
            "reported_ni": rni,
            "reval": rev,
            "interest": inx,
            "adj_ni": adj,
            "adj_ni_no_debt": adj_no_debt
        })
    
    return rows


def build_aligned_sec_series() -> List[Dict[str, Any]]:
    """
    Build aligned SEC series for last 8 quarters: NetIncomeLoss, InterestExpense, DigitalAssetReval.
    Returns list of dicts with matching end dates.
    """
    # Fetch quarterly data for each concept
    ni = fetch_sec_quarterly_values("NetIncomeLoss", n=8)
    ie = fetch_sec_quarterly_values("InterestExpense", n=8)
    
    # Try different reval concepts
    reval = None
    for concept in ("NetRealizedAndUnrealizedGainLossOnInvestments", 
                   "UnrealizedGainLossOnInvestments", 
                   "RealizedGainLossOnInvestments"):
        reval = fetch_sec_quarterly_values(concept, n=8)
        if reval:
            break
    
    # If no standard reval, try custom digital asset concepts
    if not reval:
        custom = fetch_sec_latest_custom_reval(8)
        reval = [{"end": x["end"], "val": x["val"]} for x in custom]
    
    if not (ni and ie and reval):
        return []
    
    # Index by end date for easy lookup
    def index_by_end(xs):
        return {x["end"]: x["val"] for x in xs if x.get("end") and x.get("val") is not None}
    
    i_ni = index_by_end(ni)
    i_ie = index_by_end(ie)
    i_rev = index_by_end(reval)
    
    # Find common periods (all three concepts must have data)
    common_periods = sorted(set(i_ni.keys()) & set(i_ie.keys()) & set(i_rev.keys()))
    
    # Build aligned rows
    rows = []
    for end in common_periods:
        ni_val = i_ni[end]
        reval_val = i_rev[end]
        interest_val = i_ie[end]
        
        # Core earnings = NI - Reval + Interest
        core_q = ni_val - reval_val + interest_val
        
        rows.append({
            "period": end,
            "net_income": ni_val,
            "digital_asset_reval": reval_val,
            "interest_expense": interest_val,
            "core_earnings": core_q
        })
    
    return rows


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
        
        # Display normalization status
        if sec_data:
            btc_reval = sec_data.get("btc_reval")
            interest = sec_data.get("interest")
            if btc_reval is not None:
                print(f"   BTC Reval: ${btc_reval:,.0f} | Adj NI: ${financials['reported_ni'] - btc_reval:,.0f}")
            else:
                print("   ⚠️  BTC revaluation data not available from SEC")
            
            if interest is not None:
                if btc_reval is not None:
                    adj_ni_no_debt = (financials['reported_ni'] - btc_reval) + interest
                    print(f"   Interest: ${interest:,.0f} | Adj NI (no debt): ${adj_ni_no_debt:,.0f}")
                else:
                    print(f"   Interest: ${interest:,.0f}")
            else:
                print("   ⚠️  Interest expense data not available from SEC")
        else:
            print("   ⚠️  SEC data unavailable - cannot normalize")
    
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

    # Use SEC NI only for normalization
    sec_ni = sec_data.get("net_income") if sec_data else None
    metrics["reported_ni"] = sec_ni
    metrics["reported_ni_source"] = "SEC"

    if sec_data:
        metrics["btc_reval"] = sec_data.get("btc_reval")
        metrics["btc_reval_period"] = sec_data.get("btc_reval_period")
        metrics["interest"] = sec_data.get("interest")
        metrics["interest_period"] = sec_data.get("interest_period")

    # Calculate ACMPE-TTM (Allworth Core Mining P/E) with ASU 2023-08 gating
    # Get strict P&L reval series and check ASU compliance
    strict_reval = sec_reval_series_strict(12)
    ni_series = fetch_sec_quarterly_values("NetIncomeLoss", 12)
    ie_series = fetch_sec_quarterly_values("InterestExpense", 12)
    
    # Build aligned periods with ASU gating
    aligned = sorted(set(ni.get("end") for ni in ni_series) & 
                    set(strict_reval.keys()) & 
                    set(ie.get("end") for ie in ie_series))
    
    post_asu_aligned = [p for p in aligned if post_asu(p)]
    
    # Build core earnings rows for aligned periods
    rows = []
    for end in post_asu_aligned:
        ni_val = next((item["val"] for item in ni_series if item["end"] == end), 0)
        reval_val = strict_reval[end]["val"]
        ie_val = next((item["val"] for item in ie_series if item["end"] == end), 0)
        core = ni_val - reval_val + ie_val
        rows.append({"period": end, "core": core})
    
    # Calculate RBV
    rbv = market_cap - (treasury_value + cash - total_debt)
    metrics["rbv"] = rbv
    
    # TTM only if 4 quarters available
    if len(rows) >= 4:
        core_ttm = sum(r["core"] for r in rows[-4:])
        metrics["core_ttm"] = core_ttm
        metrics["acmpe_ttm"] = (rbv / core_ttm) if (rbv > 0 and core_ttm > 0) else None
        print(f"   ✅ ACMPE-TTM calculated from {len(rows)} post-ASU aligned quarters")
    else:
        metrics["core_ttm"] = None
        metrics["acmpe_ttm"] = None
        # Optional run-rate (annualize last aligned quarter) — LABEL IT CLEARLY
        if rows and rbv > 0 and rows[-1]["core"] > 0:
            metrics["acmpe_runrate"] = rbv / (rows[-1]["core"] * 4)
            print(f"   ⚠️  ACMPE-TTM: Need 4 post-ASU aligned quarters (found {len(rows)})")
            print(f"   📊 ACMPE-RunRate (last qtr ×4): {metrics['acmpe_runrate']:.1f}x")
        else:
            metrics["acmpe_runrate"] = None
            print(f"   ⚠️  ACMPE-TTM: Need 4 post-ASU aligned quarters (found {len(rows)})")

    # === Forward Projection Scenarios (real parameters) ===
    base_params = {
        "mara_eh": 25.0,               # MARA fleet ~25 EH/s (Q4 2024)
        "network_eh": 650.0,           # Network ~650 EH/s (7-day avg)
        "btc_price": btc_price,
        "fee_pct_of_subsidy": 0.15,    # 15% fee uplift (post-halving)
        "efficiency_j_per_th": 25.0,   # J/TH (fleet-weighted average)
        "power_cost_per_mwh": 65.0,    # $/MWh (Texas average)
        "other_opex_per_q": 45_000_000, # $45M/q (excluding power)
        "depr_per_q": 35_000_000,      # $35M/q depreciation
        "interest_per_q": 25_000_000   # $25M/q interest expense
    }
    bear_params = { **base_params, "btc_price": btc_price*0.85, "fee_pct_of_subsidy": 0.05 }
    bull_params = { **base_params, "btc_price": btc_price*1.15, "fee_pct_of_subsidy": 0.20 }

    scenarios = [
        ("Bear", bear_params),
        ("Base", base_params),
        ("Bull", bull_params),
    ]

    proj_rows = []
    if SHOW_FORWARD and params_quality_ok(base_params):
        # Run forward projections only with credible inputs
        for name, p in scenarios:
            res = project_core_q(p)
            acmpe_fwd = compute_acmpe_fwd(market_cap, treasury_value, cash, total_debt, res["core_q"])
            proj_rows.append({
                "name": name,
                "btc_mined": res["btc_mined"],
                "revenue": res["revenue"],
                "power_cost": res["power_cost"],
                "core_q": res["core_q"],
                "acmpe_fwd": acmpe_fwd
            })
        
        # Put Base scenario ACMPE-FWD into metrics
        base_acmpe_fwd = next((r["acmpe_fwd"] for r in proj_rows if r["name"] == "Base"), None)
        metrics["acmpe_fwd"] = base_acmpe_fwd
    else:
        metrics["acmpe_fwd"] = None  # hide forward metric unless inputs are credible

    # Only compute Adjusted NI when periods match and reval is P&L (not balance sheet)
    ni_p = sec_data.get("ni_period") if sec_data else None
    rev_p = sec_data.get("btc_reval_period") if sec_data else None
    int_p = sec_data.get("interest_period") if sec_data else None

    if ni_p and rev_p and int_p and (ni_p == rev_p == int_p):
        # Check if reval is P&L style (not balance sheet levels)
        reval_concept = sec_data.get("btc_reval_concept", "")
        if reval_concept and looks_like_reval_pnl(reval_concept):
            adj = metrics["reported_ni"] - metrics["btc_reval"]
            adj_no_debt = adj + metrics["interest"]
            metrics["adj_ni"] = adj
            metrics["adj_ni_no_debt"] = adj_no_debt
            print(f"   ✅ Adjusted NI calculated with P&L reval: {reval_concept}")
        else:
            print(f"   ⚠️  Skipping Adjusted NI: reval concept '{reval_concept}' is not P&L style")
            metrics["adj_ni"] = None
            metrics["adj_ni_no_debt"] = None
    else:
        print(f"   ⚠️  Skipping Adjusted NI: periods don't align (NI: {ni_p}, Reval: {rev_p}, Interest: {int_p})")
        metrics["adj_ni"] = None
        metrics["adj_ni_no_debt"] = None

    # Evaluate & decide
    crit = DecisionCriteria()
    eval_out = evaluate_signals(metrics, crit)
    
    # Tighten the TL;DR gate (avoid false BUYs)
    # Require discount + reasonable multiple + data alignment
    if (metrics.get("mnav") is not None and metrics["mnav"] <= 0.95
        and metrics.get("acmpe_ttm") is not None and metrics["acmpe_ttm"] <= 18):
        decision = {"action": "BUY", "summary": "mNAV discount + reasonable ACMPE-TTM."}
    elif metrics.get("mnav") is not None and metrics["mnav"] > 1.10:
        decision = {"action": "HOLD/AVOID", "summary": "Premium to treasury; wait for discount or better core outlook."}
    else:
        decision = {"action": "NEUTRAL", "summary": "Mixed signals or missing aligned data."}

    # Build and print the explainer + TL;DR
    report = build_report(metrics, eval_out, decision, sec_data, proj_rows)
    print("\n" + "="*60)
    print(report)
    
    # Show exactly what the email would look like
    print("\n" + "="*60)
    print("📧 EMAIL PREVIEW (what would be sent)")
    print("="*60)
    
    # Enhanced subject with key metrics (ACMPE-FWD only if enabled and credible)
    acmpe = metrics.get('acmpe_ttm')
    acmpe_fwd = metrics.get('acmpe_fwd')
    acmpe_str = f"ACMPE:{acmpe:.1f}x" if acmpe else "ACMPE:N/A"
    
    if acmpe_fwd is not None:
        email_subject = f"MARA Signal — {decision['action']} | mNAV:{mnav:.2f}x | {acmpe_str} | ACMPE-FWD:{acmpe_fwd:.1f}x"
    else:
        email_subject = f"MARA Signal — {decision['action']} | mNAV:{mnav:.2f}x | {acmpe_str}"
    
    print(f"SUBJECT: {email_subject}")
    print("-" * 60)
    print("RECIPIENTS: " + (os.getenv("ALERT_RECIPIENTS", "Not configured") or "Not configured"))
    print("-" * 60)
    print("BODY:")
    print(report)
    print("="*60)

    # Optional: email if user configured recipients and state changed
    recipients_env = os.getenv("ALERT_RECIPIENTS", "")
    recipients = [e.strip() for e in recipients_env.split(",") if e.strip()]
    if recipients:
        # Get current period for state tracking
        current_period = metrics.get('reported_ni_period') or "unknown"
        
        if should_send_email(decision['action'], current_period):
            # Enhanced subject with key metrics (ACMPE-FWD only if enabled and credible)
            acmpe = metrics.get('acmpe_ttm')
            acmpe_fwd = metrics.get('acmpe_fwd')
            acmpe_str = f"ACMPE:{acmpe:.1f}x" if acmpe else "ACMPE:N/A"
            
            if acmpe_fwd is not None:
                subject = f"MARA Signal — {decision['action']} | mNAV:{mnav:.2f}x | {acmpe_str} | ACMPE-FWD:{acmpe_fwd:.1f}x"
            else:
                subject = f"MARA Signal — {decision['action']} | mNAV:{mnav:.2f}x | {acmpe_str}"
            send_email_report(report, subject, recipients)
        else:
            print("📧 Email skipped — no change in action or period")
    
    print("\n[C] Forward Projection — ✅ COMPLETE")
    print("[D] Valuation — TODO")
    print(f"Action — {decision['action']}")
    
    # Show configuration instructions if email not set up
    if not os.getenv("ALERT_RECIPIENTS"):
        print("\n" + "="*60)
        print("📧 EMAIL SETUP INSTRUCTIONS")
        print("="*60)
        print("To enable email alerts, set these environment variables:")
        print("")
        print("export SMTP_HOST='smtp.office365.com'")
        print("export SMTP_PORT='587'")
        print("export SMTP_USER='you@example.com'")
        print("export SMTP_PASS='app_password'")
        print("export SMTP_FROM='you@example.com'")
        print("export ALERT_RECIPIENTS='friend1@example.com,friend2@example.com'")
        print("")
        print("Then run: python3 mara_val.py")
        print("="*60)
    
    # Show forward model instructions
    if not SHOW_FORWARD:
        print("\n" + "="*60)
        print("🚀 FORWARD MODEL SETUP")
        print("="*60)
        print("To enable forward projections (ACMPE-FWD), set:")
        print("")
        print("export SHOW_FORWARD=1")
        print("")
        print("Then update the base_params in the code with real inputs:")
        print("• MARA hashrate (EH/s) from quarterly reports")
        print("• Network hashrate (EH/s) from blockchain data")
        print("• Fleet efficiency (J/TH) from operations")
        print("• Power costs ($/MWh) from energy contracts")
        print("• Operating expenses from financial statements")
        print("="*60)

if __name__ == "__main__":
    main()
