
# Bitcoin Treasury Lightning Network EPS Calculator
# Tool for CFOs to demonstrate non-dilutive EPS and sats per share improvements

def calculate_lightning_yield_impact(
    total_btc_reserves, 
    lightning_annual_yield, 
    traditional_annual_yield,
    shares_outstanding,
    years,
    lightning_allocation_percent=0.10  # Default 10% allocation to Lightning
):
    """
    Calculate the impact of Lightning Network yield strategies on EPS and sats per share.
    
    Args:
        total_btc_reserves: Company's total BTC holdings
        btc_price: Current BTC price in USD
        lightning_annual_yield: Annual yield from Lightning Network strategies
        traditional_annual_yield: Current yield from traditional BTC holdings
        shares_outstanding: Number of shares outstanding
        years: Time horizon for projection
        lightning_allocation_percent: Percentage of BTC allocated to Lightning (0.0-1.0)
    """
    
    # Calculate allocations
    lightning_btc = total_btc_reserves * lightning_allocation_percent
    traditional_btc = total_btc_reserves * (1 - lightning_allocation_percent)
    
    # Monthly yields
    lightning_monthly_yield = lightning_annual_yield / 12
    traditional_monthly_yield = traditional_annual_yield / 12
    
    # Initial values
    lightning_balance = lightning_btc
    traditional_balance = traditional_btc
    total_btc_balance = total_btc_reserves
    
    results = []
    
    for month in range(1, years * 12 + 1):
        # Calculate yields
        lightning_yield = lightning_balance * lightning_monthly_yield
        traditional_yield = traditional_balance * traditional_monthly_yield
        
        # Update balances
        lightning_balance += lightning_yield
        traditional_balance += traditional_yield
        total_btc_balance = lightning_balance + traditional_balance
        
        # Calculate EPS and sats per share (Bitcoin-focused)
        total_earnings_btc = lightning_yield + traditional_yield
        eps = total_earnings_btc / shares_outstanding
        sats_per_share = total_earnings_btc * 100_000_000 / shares_outstanding  # Monthly sats per share
        
        # Calculate improvement vs traditional-only strategy
        traditional_only_earnings = traditional_btc * traditional_monthly_yield
        traditional_only_eps = traditional_only_earnings / shares_outstanding
        eps_improvement = eps - traditional_only_eps
        eps_improvement_percent = (eps_improvement / traditional_only_eps * 100) if traditional_only_eps > 0 else 0
        
        results.append({
            'month': month,
            'lightning_btc': lightning_balance,
            'traditional_btc': traditional_balance,
            'total_btc': total_btc_balance,
            'monthly_earnings_btc': total_earnings_btc,
            'eps': eps,
            'sats_per_share': sats_per_share,
            'eps_improvement': eps_improvement,
            'eps_improvement_percent': eps_improvement_percent
        })
    
    return results

def print_cfo_report(results, initial_params):
    """Generate a concise Lightning-yield briefing for CFOs/CEOs."""
    
    line = "-" * 72
    print(f"\n{line}")
    print("LIGHTNING YIELD – EPS IMPACT BRIEF")
    print(f"{line}\n")
    
    # 1. Starting point
    print("1. Treasury Snapshot")
    print(f"   • Bitcoin on balance sheet : {initial_params['total_btc_reserves']:.8f} BTC")
    print(f"   • Shares outstanding       : {initial_params['shares_outstanding']:,}")
    print(f"   • Proposed Lightning slice : {initial_params['lightning_allocation_percent']*100:.1f}% (initial pilot)")
    print("")
    
    # 2. Yield assumptions
    print("2. Yield Assumptions (Annualised)")
    print(f"   • Current passive yield    : {initial_params['traditional_annual_yield']*100:.2f}%")
    print(f"   • Lightning routing yield  : {initial_params['lightning_annual_yield']*100:.2f}%")
    print(f"   • Yield improvement        : from {initial_params['traditional_annual_yield']*100:.1f}% to {initial_params['lightning_annual_yield']*100:.1f}% (>∞% relative gain)\n")
    
    # 3. Quarterly EPS projections (entire timeline)
    print("3. Projected EPS Contribution (sats per share)")
    print(f"{'Quarter':<10} {'Incremental EPS':>18}")
    print("-" * 32)
    for result in results[::3][:8]:  # first eight quarters only
        qtr = (result['month'] - 1) // 3 + 1
        yr = (result['month'] - 1) // 12 + 1
        label = f"Q{qtr}-Y{yr}"
        # Calculate quarterly EPS (monthly * 3)
        quarterly_eps_sats = result['sats_per_share'] * 3
        print(f"{label:<10} {quarterly_eps_sats:>18,.0f}")
    
    # 4. Five-year headline metrics
    final = results[-1]
    btc_growth = (final['total_btc'] / initial_params['total_btc_reserves'] - 1) * 100
    print("\n4. Five-Year Headline Metrics")
    print(f"   • BTC holdings after 5 yr   : {final['total_btc']:.6f} BTC ({btc_growth:.2f}% growth)")
    print(f"   • Annual EPS from LN yield — Year 5: {final['sats_per_share']*12:,.0f} sats per share")
    print(f"   • Cumulative EPS (5 yrs)   : {final['sats_per_share']*12*5:,.0f} sats per share")
    
    # Company-wide earnings impact
    lightning_btc = initial_params['total_btc_reserves'] * initial_params['lightning_allocation_percent']
    annual_lightning_earnings_btc = lightning_btc * initial_params['lightning_annual_yield']
    total_company_annual_earnings_btc = annual_lightning_earnings_btc
    total_company_5yr_earnings_btc = total_company_annual_earnings_btc * 5
    
    print(f"   • Company annual earnings   : {total_company_annual_earnings_btc:.6f} BTC from Lightning")
    print(f"   • Company 5-yr earnings     : {total_company_5yr_earnings_btc:.6f} BTC total\n")
    
    # 5. Key advantages
    print("5. Why Lightning vs. Traditional BTC or High-Yield DeFi?")
    print("   • Non-custodial – coins remain in      client-controlled multi-sig")
    print("   • Risk profile – no rehypothecation,   no smart-contract exploits")
    print("   • GAAP benefit – sat income reported   under ASC 350-60 each quarter")
    print("   • Shareholder optics – BTC-per-share   grows without dilution\n")
    
    # 6. mNAV and investor interest advantage
    print("6. Market NAV Premium & Share Dilution Strategy")
    print("   • Lightning yield creates measurable EPS growth vs. passive BTC holders")
    print("   • Measured growth attracts investor interest = higher mNAV premium")
    print("   • Higher mNAV enables more profitable ATM share dilution")
    print("   • Sell shares at premium while maintaining strong sats-per-share growth")
    print("   • Use ATM proceeds to acquire more BTC at market prices")
    print("   • Reinvest additional BTC into Lightning = compound growth cycle")
    print("   • Competitive differentiation: Other BTC holders can't match this yield")
    print("   • Competitive edge: Mega-holders (>10k BTC) can't replicate this today")
    print("   • Mid-sized treasuries (1-5k BTC) enjoy temporary, high-margin opportunity\n")
    
    # 7. Why Act Now
    print("7. Why Act Now")
    print("   • Accounting tailwind: ASC 350-60 (effective FY 2025) first cycle for Lightning EPS")
    print("   • Early adopters publish first 'Lightning EPS' lines in Q1 2026 earnings")
    print("   • Later entrants become 'me-too' - diminishing headline value")
    print("   • Yield spreads will compress: 3-5% today → 2% or less as capacity grows")
    print("   • Piloting in 2025-26 locks in the fat end of the yield curve")
    print("   • Network capacity favors mid-sized stacks (500 BTC = meaningful for 5k treasury)")
    print("   • Size arbitrage disappears once Lightning capacity triples")
    print("   • First-mover mNAV premium: Investors reward first corporate actions")
    print("   • Learning-curve moat: Operational playbooks take quarters to perfect")
    print("   • Net cost of delay: Higher spreads + lost valuation pop + lost learning year\n")
    
    print(line)
    
    return final

def get_cfo_inputs():
    """Interactive input function for CFOs to enter their parameters"""
    print("\n" + "="*80)
    print("BITCOIN TREASURY LIGHTNING NETWORK EPS CALCULATOR")
    print("="*80)
    print("\nEnter your corporate treasury parameters:")
    
    # Corporate Treasury Stats
    total_btc_reserves = float(input("\n📊 Total BTC Reserves: ") or "1000.0")
    shares_outstanding = float(input("📊 Shares Outstanding: ") or "10000000")
    
    # Yield Parameters
    print(f"\n💰 YIELD PARAMETERS:")
    current_yield_zero = input("   Is your current BTC yield 0%? (y/n): ").lower().strip()
    if current_yield_zero == 'y' or current_yield_zero == '':
        traditional_annual_yield = 0.0
        print("   ✓ Traditional BTC Yield set to 0%")
    else:
        traditional_annual_yield = float(input("   Enter your current BTC yield (% annually): ")) / 100
    lightning_annual_yield = float(input("   Lightning Network Yield (% annually, expect 2-6%, Block recently demonstrated 9.7%): ") or "4.0") / 100
    
    # Strategy Parameters
    lightning_allocation_percent = float(input(f"\n⚡ Lightning Allocation (% of BTC Treasury): ") or "10.0") / 100
    years = int(input("📅 Time Horizon (years): ") or "5")
    
    return {
        'total_btc_reserves': total_btc_reserves,
        'lightning_annual_yield': lightning_annual_yield,
        'traditional_annual_yield': traditional_annual_yield,
        'shares_outstanding': shares_outstanding,
        'lightning_allocation_percent': lightning_allocation_percent,
        'years': years
    }



if __name__ == "__main__":
    # Get CFO inputs interactively
    initial_params = get_cfo_inputs()
    
    # Calculate results
    results = calculate_lightning_yield_impact(**initial_params)
    
    # Generate CFO report
    final_results = print_cfo_report(results, initial_params)
    
    # Interactive mode for testing different yields
    while True:
        print(f"\n" + "="*50)
        test_again = input("\n🔧 Test different yields? (y/n): ").lower()
        if test_again != 'y':
            break
            
        print(f"\n💰 TEST DIFFERENT YIELD SCENARIOS:")
        new_lightning_yield = float(input("   New Lightning Network Yield (% annually): ")) / 100
        new_traditional_yield = float(input("   New Traditional BTC Yield (% annually): ")) / 100
        
        test_params = initial_params.copy()
        test_params['lightning_annual_yield'] = new_lightning_yield
        test_params['traditional_annual_yield'] = new_traditional_yield
        
        test_results = calculate_lightning_yield_impact(**test_params)
        final_eps_improvement = test_results[-1]['eps_improvement_percent']
        
        print(f"\n📊 QUICK RESULTS:")
        print(f"   EPS Improvement: {final_eps_improvement:.1f}%")
        print(f"   Final Quarterly EPS: {test_results[-1]['sats_per_share']*3:.0f} sats")
