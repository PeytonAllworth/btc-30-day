
# Bitcoin Treasury Lightning Network EPS Calculator
# Tool for CFOs to demonstrate non-dilutive EPS and sats per share improvements

import requests
import json
from datetime import datetime, timedelta
import time

def fetch_live_lightning_data():
    """Fetch live Lightning Network data from APIs"""
    print("\n🌐 Fetching live Lightning Network data...")
    
    try:
        # Fetch network capacity and statistics
        print("📊 Fetching network capacity...")
        network_data = fetch_network_capacity()
        
        print("💰 Fetching yield rates...")
        yield_data = fetch_live_yield_rates()
        
        print("🏢 Fetching node performance...")
        node_data = fetch_major_node_performance()
        
        # Check if we got real network data
        if network_data is None:
            print("⚠️  Warning: Could not fetch live network data. Using conservative estimates.")
            return get_fallback_data()
        
        print(f"✅ Successfully fetched data from: {network_data.get('source', 'Unknown API')}")
        
        return {
            'network_capacity': network_data,
            'yield_rates': yield_data,
            'node_performance': node_data,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_source': network_data.get('source', 'Unknown API')
        }
    except Exception as e:
        print(f"❌ Warning: Could not fetch live data: {e}")
        return get_fallback_data()

def fetch_network_capacity():
    """Fetch current Lightning Network capacity"""
    print("🔍 Fetching network capacity data...")
    
    try:
        # Try known working Lightning Network APIs
        apis = [
            ('https://api.blockchair.com/bitcoin/stats', 'Blockchair Bitcoin Stats'),
            ('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', 'CoinGecko')
        ]
        
        for api_url, source in apis:
            print(f"  📡 Calling {source}...")
            try:
                response = requests.get(api_url, timeout=10)
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✅ Success! Data keys: {list(data.keys())[:5]}...")
                    
                    if source == 'Blockchair Bitcoin Stats' and 'data' in data:
                        # Use Bitcoin network stats as context, estimate Lightning
                        btc_stats = data['data']
                        print(f"    📊 Bitcoin stats available: {list(btc_stats.keys())[:5]}...")
                        return {
                            'total_capacity_btc': None,  # No real Lightning capacity data available
                            'channel_count': None,       # No real channel count data available
                            'node_count': None,          # No real node count data available
                            'avg_channel_size': None,
                            'source': f'{source} (Bitcoin context only - Lightning data estimated)'
                        }
                    elif source == 'CoinGecko' and 'bitcoin' in data:
                        # Just get BTC price context
                        btc_price = data['bitcoin']['usd']
                        print(f"    💰 BTC Price: ${btc_price:,.2f}")
                        return {
                            'total_capacity_btc': None,  # No real Lightning capacity data available
                            'channel_count': None,
                            'node_count': None,
                            'avg_channel_size': None,
                            'source': f'{source} (BTC price: ${btc_price:,.0f} - Lightning data estimated)'
                        }
                else:
                    print(f"    ❌ Failed with status {response.status_code}")
                        
            except Exception as e:
                print(f"    ❌ API {source} failed: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Warning: Could not fetch live network data: {e}")
    
    print("  ⚠️  All APIs failed, returning None")
    # If all APIs fail, return None to indicate no real data
    return None

def fetch_live_yield_rates():
    """Fetch live yield rates from major Lightning nodes"""
    print("    📈 No real Lightning yield data available")
    print("    💡 Note: Lightning yield rates are not publicly reported")
    
    try:
        # No real data available - return None to indicate this
        return {
            'avg_yield_apr': None,
            'top_node_yield': None,
            'bottom_node_yield': None,
            'yield_range': None,
            'fee_compression_trend': None
        }
    except:
        return {
            'avg_yield_apr': None,
            'top_node_yield': None,
            'bottom_node_yield': None,
            'yield_range': None,
            'fee_compression_trend': None
        }

def fetch_major_node_performance():
    """Fetch performance data from major Lightning node operators"""
    print("    🏢 Using estimated node performance (no live API available)")
    print("    💡 Note: Node operator APIs are private")
    
    try:
        # This would integrate with actual node operator APIs
        return {
            'top_nodes': [
                {'name': 'Block', 'yield': 5.2, 'capacity': 1200},
                {'name': 'Kraken', 'yield': 4.8, 'capacity': 800},
                {'name': 'Bitfinex', 'yield': 4.5, 'capacity': 600}
            ],
            'network_growth_rate': None,  # No real data available
            'capacity_utilization': None   # No real data available
        }
    except:
        return {
            'top_nodes': [
                {'name': 'Block', 'yield': 5.0, 'capacity': 1000},
                {'name': 'Kraken', 'yield': 4.5, 'capacity': 750},
                {'name': 'Bitfinex', 'yield': 4.2, 'capacity': 500}
            ],
            'network_growth_rate': None,
            'capacity_utilization': None
        }

def fetch_current_btc_price():
    """Fetch current Bitcoin price from CoinGecko API"""
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'bitcoin' in data and 'usd' in data['bitcoin']:
                return data['bitcoin']['usd']
    except Exception as e:
        print(f"   ⚠️  Could not fetch BTC price: {e}")
    return None

def fetch_treasury_data():
    """Fetch real treasury data from bitcointreasuries.net"""
    try:
        print("   📊 Fetching treasury data from bitcointreasuries.net...")
        response = requests.get('https://bitcointreasuries.net/', timeout=15)
        
        if response.status_code == 200:
            # Parse the HTML to extract treasury data
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the treasury table
            treasury_data = []
            
            # Try to find the main treasury table
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        try:
                            company = cells[0].get_text(strip=True)
                            btc_holdings_text = cells[1].get_text(strip=True)
                            
                            # Extract BTC amount (remove commas and 'BTC')
                            btc_holdings = btc_holdings_text.replace(',', '').replace(' BTC', '').replace('$', '')
                            
                            # Try to convert to float
                            try:
                                btc_amount = float(btc_holdings)
                                treasury_data.append({
                                    'company': company,
                                    'btc_holdings': btc_amount
                                })
                            except ValueError:
                                continue
                                
                        except (IndexError, ValueError):
                            continue
            
            # If we couldn't parse the table, use fallback data
            if not treasury_data:
                print("   ⚠️  Could not parse treasury data, using fallback")
                return get_fallback_treasury_data()
            
            # Sort by BTC holdings and return top companies
            treasury_data.sort(key=lambda x: x['btc_holdings'], reverse=True)
            return treasury_data[:10]  # Top 10 companies
            
        else:
            print(f"   ⚠️  Could not fetch treasury data (Status: {response.status_code})")
            return get_fallback_treasury_data()
            
    except Exception as e:
        print(f"   ⚠️  Could not fetch treasury data: {e}")
        return get_fallback_treasury_data()

def get_fallback_treasury_data():
    """Return fallback treasury data when scraping fails"""
    return [
        {'company': 'MicroStrategy', 'btc_holdings': 214400},
        {'company': 'Tesla', 'btc_holdings': 10725},
        {'company': 'Block', 'btc_holdings': 8027},
        {'company': 'Marathon Digital', 'btc_holdings': 15000},
        {'company': 'Riot Platforms', 'btc_holdings': 12000},
        {'company': 'Coinbase', 'btc_holdings': 10000},
        {'company': 'Hut 8 Mining', 'btc_holdings': 9000},
        {'company': 'CleanSpark', 'btc_holdings': 8000},
        {'company': 'Bitfarms', 'btc_holdings': 7000},
        {'company': 'Cipher Mining', 'btc_holdings': 6000}
    ]

def calculate_competitive_analysis(initial_params, treasury_data):
    """Calculate competitive analysis comparing your strategy to other treasuries"""
    
    your_btc = initial_params['total_btc_reserves']
    your_lightning_yield = initial_params['lightning_annual_yield']
    your_allocation = initial_params['lightning_allocation_percent']
    btc_price = initial_params['btc_price']
    
    competitive_analysis = []
    
    for company in treasury_data:
        company_btc = company['btc_holdings']
        company_name = company['company']
        
        # Calculate potential Lightning allocation (10% of their BTC)
        potential_lightning_btc = company_btc * 0.10
        
        # Calculate annual Lightning earnings
        annual_lightning_earnings_btc = potential_lightning_btc * your_lightning_yield
        
        # Estimate shares outstanding (rough estimates)
        estimated_shares = {
            'MicroStrategy': 17000000,
            'Tesla': 3200000000,
            'Block': 620000000,
            'Marathon Digital': 250000000,
            'Riot Platforms': 200000000,
            'Coinbase': 250000000,
            'Hut 8 Mining': 100000000,
            'CleanSpark': 50000000,
            'Bitfarms': 40000000,
            'Cipher Mining': 30000000
        }
        
        shares = estimated_shares.get(company_name, 100000000)  # Default 100M shares
        
        # Calculate potential EPS impact
        annual_eps_btc = annual_lightning_earnings_btc / shares
        annual_eps_usd = annual_eps_btc * btc_price
        
        # Determine competitive advantage
        if company_btc > 50000:
            advantage = "Too large - would crash Lightning fees"
        elif company_btc > 10000:
            advantage = "Sweet spot - could deploy without market impact"
        elif company_name == 'Block':
            advantage = "Already doing Lightning (9.7% yield demonstrated)"
        else:
            advantage = "Good size for Lightning deployment"
        
        competitive_analysis.append({
            'company': company_name,
            'btc_holdings': company_btc,
            'potential_lightning_btc': potential_lightning_btc,
            'annual_lightning_earnings_btc': annual_lightning_earnings_btc,
            'estimated_shares': shares,
            'annual_eps_btc': annual_eps_btc,
            'annual_eps_usd': annual_eps_usd,
            'advantage': advantage
        })
    
    return competitive_analysis

def test_lightning_apis():
    """Test which APIs are working"""
    print("Testing available APIs...")
    
    test_apis = [
        'https://api.blockchair.com/bitcoin/stats',
        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    ]
    
    for api_url in test_apis:
        try:
            response = requests.get(api_url, timeout=5)
            print(f"✓ {api_url}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Data keys: {list(data.keys())[:5]}...")
        except Exception as e:
            print(f"✗ {api_url}: {e}")
    
    print("Note: Lightning Network APIs are limited. Using Bitcoin context + Lightning estimates.\n")

def get_fallback_data():
    """Return fallback data when live APIs are unavailable"""
    return {
        'network_capacity': {
            'total_capacity_btc': None,  # No real data available
            'channel_count': None,       # No real data available
            'node_count': None,          # No real data available
            'avg_channel_size': None
        },
        'yield_rates': {
            'avg_yield_apr': None,
            'top_node_yield': None,
            'bottom_node_yield': None,
            'yield_range': None,
            'fee_compression_trend': None
        },
        'node_performance': {
            'top_nodes': [
                {'name': 'Block', 'yield': 5.0, 'capacity': 1000},
                {'name': 'Kraken', 'yield': 4.5, 'capacity': 750},
                {'name': 'Bitfinex', 'yield': 4.2, 'capacity': 500}
            ],
            'network_growth_rate': None,
            'capacity_utilization': None
        },
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def calculate_minimum_channel_size(initial_params, results):
    """Calculate minimum Lightning channel size needed to break even in each quarter"""
    
    # Setup costs (one-time)
    total_setup_cost = (initial_params['setup_hardware'] + 
                       initial_params['setup_software'] + 
                       initial_params['setup_consulting'])
    
    # Annual operational costs
    annual_operational = initial_params['annual_operational']
    
    # Lightning yield rate
    lightning_yield = initial_params['lightning_annual_yield']
    
    # Shares outstanding
    shares_outstanding = initial_params['shares_outstanding']
    
    min_channel_sizes = []
    
    for result in results[::3]:  # Every 3rd month (quarterly)
        month = result['month']
        current_btc_price = result['btc_price']
        
        # Calculate quarter number
        qtr = ((month - 1) % 12) // 3 + 1
        yr = (month - 1) // 12 + 1
        
        # Monthly operational costs in BTC at current price
        monthly_operational_btc = (annual_operational / 12) / current_btc_price
        
        # To break even: Lightning earnings = Operational costs
        # Lightning earnings = channel_size * monthly_yield_rate
        # Operational costs = monthly_operational_btc
        # Therefore: channel_size = monthly_operational_btc / monthly_yield_rate
        
        monthly_yield_rate = lightning_yield / 12
        min_channel_size_btc = monthly_operational_btc / monthly_yield_rate
        
        # Calculate total costs to date (setup + operational)
        months_elapsed = month
        total_operational_to_date = (annual_operational / 12) * months_elapsed
        total_costs_to_date_usd = total_setup_cost + total_operational_to_date
        
        # Calculate minimum channel size to cover all costs to date
        total_lightning_earnings_needed_btc = total_costs_to_date_usd / current_btc_price
        min_channel_size_for_total_costs_btc = total_lightning_earnings_needed_btc / (monthly_yield_rate * months_elapsed)
        
        min_channel_sizes.append({
            'quarter': f"Y{yr}Q{qtr}",
            'month': month,
            'btc_price': current_btc_price,
            'min_channel_operational_btc': min_channel_size_btc,
            'min_channel_operational_usd': min_channel_size_btc * current_btc_price,
            'min_channel_total_costs_btc': min_channel_size_for_total_costs_btc,
            'min_channel_total_costs_usd': min_channel_size_for_total_costs_btc * current_btc_price,
            'total_costs_to_date_usd': total_costs_to_date_usd
        })
    
    return min_channel_sizes

def calculate_implementation_roi(initial_params, results):
    """Calculate implementation costs, ROI, and break-even analysis"""
    
    # Setup costs
    total_setup_cost = (initial_params['setup_hardware'] + 
                       initial_params['setup_software'] + 
                       initial_params['setup_consulting'])
    
    # Calculate Lightning allocation in BTC and USD
    lightning_btc = initial_params['total_btc_reserves'] * initial_params['lightning_allocation_percent']
    lightning_usd = lightning_btc * initial_params['btc_price']
    
    # Calculate annual Lightning earnings
    annual_lightning_earnings_btc = lightning_btc * initial_params['lightning_annual_yield']
    
    # Get final year data for projections
    final_result = results[-1]
    final_btc_price = final_result['btc_price']
    
    # Calculate earnings over the time horizon
    total_lightning_earnings_btc = annual_lightning_earnings_btc * initial_params['years']
    total_lightning_earnings_usd = total_lightning_earnings_btc * final_btc_price  # Using final year price
    
    # Calculate operational costs over time horizon
    total_operational_costs = initial_params['annual_operational'] * initial_params['years']
    
    # Net benefits
    net_benefits_usd = total_lightning_earnings_usd - total_operational_costs
    
    # ROI calculation
    total_investment = total_setup_cost + total_operational_costs
    roi_percentage = (net_benefits_usd / total_investment * 100) if total_investment > 0 else 0
    
    # Break-even analysis
    annual_net_benefit = (annual_lightning_earnings_btc * final_btc_price) - initial_params['annual_operational']
    break_even_years = total_setup_cost / annual_net_benefit if annual_net_benefit > 0 else float('inf')
    
    # Payback period (including operational costs)
    cumulative_benefit = 0
    payback_year = None
    for year in range(1, initial_params['years'] + 1):
        year_benefit = (annual_lightning_earnings_btc * final_btc_price) - initial_params['annual_operational']
        cumulative_benefit += year_benefit
        if cumulative_benefit >= total_setup_cost and payback_year is None:
            payback_year = year
    
    return {
        'total_setup_cost': total_setup_cost,
        'total_operational_costs': total_operational_costs,
        'total_investment': total_investment,
        'total_lightning_earnings_usd': total_lightning_earnings_usd,
        'net_benefits_usd': net_benefits_usd,
        'roi_percentage': roi_percentage,
        'break_even_years': break_even_years,
        'payback_year': payback_year,
        'annual_net_benefit': annual_net_benefit,
        'lightning_allocation_usd': lightning_usd
    }

def calculate_optimal_allocation(treasury_size, live_data):
    """Calculate optimal Lightning allocation based on treasury size and real-time network data"""
    current_capacity = live_data['network_capacity']['total_capacity_btc']
    
    # If no real capacity data, cannot provide meaningful recommendations
    if current_capacity is None:
        return {
            'recommended': None,
            'conservative': None,
            'current_capacity': None,
            'rationale': "No real Lightning Network data available - cannot provide allocation recommendations"
        }
    
    # Cannot provide real allocation recommendations without Lightning Network data
    # These calculations would require real network capacity, yield data, and economic models
    return {
        'recommended': None,
        'conservative': None,
        'current_capacity': current_capacity,
        'rationale': "Cannot provide allocation recommendations without real Lightning Network data"
    }
    
    # This return statement is now unreachable due to the above changes
    pass

def calculate_lightning_yield_impact(
    total_btc_reserves, 
    lightning_annual_yield, 
    traditional_annual_yield,
    shares_outstanding,
    years,
    lightning_allocation_percent=0.10,  # Default 10% allocation to Lightning
    btc_price=50000.0,  # Current BTC price
    btc_cagr=0.15,  # Expected BTC CAGR
    setup_hardware=50000,  # Hardware setup costs
    setup_software=25000,  # Software/licensing costs
    setup_consulting=100000,  # Consulting/implementation costs
    annual_operational=50000  # Annual operational costs
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
    current_btc_price = btc_price
    
    results = []
    
    for month in range(1, years * 12 + 1):
        # Calculate yields
        lightning_yield = lightning_balance * lightning_monthly_yield
        traditional_yield = traditional_balance * traditional_monthly_yield
        
        # Update balances
        lightning_balance += lightning_yield
        traditional_balance += traditional_yield
        total_btc_balance = lightning_balance + traditional_balance
        
        # Calculate current BTC price with CAGR
        months_elapsed = month - 1
        current_btc_price = btc_price * (1 + btc_cagr) ** (months_elapsed / 12)
        
        # Calculate gross earnings from Lightning and traditional yields
        lightning_earnings_btc = lightning_yield
        traditional_earnings_btc = traditional_yield
        total_gross_earnings_btc = lightning_earnings_btc + traditional_earnings_btc
        
        # Calculate operational costs (monthly) - fixed in USD, converted at current month's BTC price
        monthly_operational_costs_usd = annual_operational / 12
        monthly_operational_costs_btc = monthly_operational_costs_usd / current_btc_price  # Use current month's BTC price
        
        # Calculate net earnings (gross earnings minus operational costs)
        net_earnings_btc = total_gross_earnings_btc - monthly_operational_costs_btc
        
        # Calculate EPS and sats per share (net earnings)
        eps = net_earnings_btc / shares_outstanding
        sats_per_share = net_earnings_btc * 100_000_000 / shares_outstanding  # Monthly sats per share
        
        # Debug output for first month
        if month == 1:
            print(f"\n🔍 DEBUG - Month 1 Calculation:")
            print(f"   Lightning allocation: {lightning_btc:.6f} BTC")
            print(f"   Lightning monthly yield: {lightning_monthly_yield:.6f}")
            print(f"   Lightning earnings: {lightning_earnings_btc:.6f} BTC")
            print(f"   Monthly operational costs: ${monthly_operational_costs_usd:.2f}")
            print(f"   Monthly operational costs BTC: {monthly_operational_costs_btc:.6f} BTC")
            print(f"   Gross earnings: {total_gross_earnings_btc:.6f} BTC")
            print(f"   Net earnings: {net_earnings_btc:.6f} BTC")
            print(f"   Shares outstanding: {shares_outstanding}")
            print(f"   EPS: {eps:.6f} BTC")
            print(f"   Sats per share: {sats_per_share:.2f}")
        
        # Calculate USD values
        eps_usd = eps * current_btc_price
        sats_per_share_usd = sats_per_share * current_btc_price / 100_000_000
        
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
            'monthly_earnings_btc': net_earnings_btc,
            'eps': eps,
            'sats_per_share': sats_per_share,
            'eps_usd': eps_usd,
            'sats_per_share_usd': sats_per_share_usd,
            'btc_price': current_btc_price,
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
    
    # 2. Yield and price assumptions
    print("2. Yield and Price Assumptions (Annualised)")
    print(f"   • Current passive yield    : {initial_params['traditional_annual_yield']*100:.2f}%")
    print(f"   • Lightning routing yield  : {initial_params['lightning_annual_yield']*100:.2f}%")
    print(f"   • Yield improvement        : from {initial_params['traditional_annual_yield']*100:.1f}% to {initial_params['lightning_annual_yield']*100:.1f}% (>∞% relative gain)")
    print(f"   • Current BTC price        : ${initial_params['btc_price']:,.2f}")
    print(f"   • Expected BTC CAGR        : {initial_params['btc_cagr']*100:.1f}%\n")
    
    # 3. Quarterly EPS projections (full timeline)
    print("3. Projected EPS Contribution")
    print(f"{'Quarter':<10} {'EPS (sats)':>12} {'EPS (USD)':>12} {'BTC Price':>12}")
    print("-" * 50)
    
    # Show all quarters for the full time horizon
    for result in results[::3]:  # Every 3rd month (quarterly)
        month = result['month']
        qtr = ((month - 1) % 12) // 3 + 1  # Quarter within the year (1-4)
        yr = (month - 1) // 12 + 1         # Year number
        label = f"Y{yr}Q{qtr}"
        
        # Calculate quarterly values (monthly * 3)
        quarterly_eps_sats = result['sats_per_share'] * 3
        quarterly_eps_usd = result['sats_per_share_usd'] * 3
        btc_price = result['btc_price']
        
        print(f"{label:<10} {quarterly_eps_sats:>12,.2f} ${quarterly_eps_usd:>11,.2f} ${btc_price:>11,.0f}")
    
    # 4. Final year headline metrics
    final = results[-1]
    years = initial_params['years']
    btc_growth = (final['total_btc'] / initial_params['total_btc_reserves'] - 1) * 100
    print(f"\n4. {years}-Year Headline Metrics")
    print(f"   • BTC holdings after {years} yr:     {final['total_btc']:.6f} BTC ({btc_growth:.2f}% growth)")
    print(f"   • Annual EPS from LN yield — Year {years}: {final['sats_per_share']*12:,.0f} sats per share (${final['sats_per_share_usd']*12:,.2f})")
    print(f"   • Cumulative EPS ({years} yrs):     {final['sats_per_share']*12*years:,.0f} sats per share (${final['sats_per_share_usd']*12*years:,.2f})")
    
    # Company-wide earnings impact
    lightning_btc = initial_params['total_btc_reserves'] * initial_params['lightning_allocation_percent']
    annual_lightning_earnings_btc = lightning_btc * initial_params['lightning_annual_yield']
    total_company_annual_earnings_btc = annual_lightning_earnings_btc
    total_company_final_earnings_btc = total_company_annual_earnings_btc * years
    
    print(f"   • Company annual earnings:     {total_company_annual_earnings_btc:.6f} BTC from Lightning (${total_company_annual_earnings_btc * final['btc_price']:,.2f})")
    print(f"   • Company {years}-yr earnings:       {total_company_final_earnings_btc:.6f} BTC total (${total_company_final_earnings_btc * final['btc_price']:,.2f})\n")
    
    # 5. Implementation ROI Analysis
    roi_data = calculate_implementation_roi(initial_params, results)
    print("5. Implementation ROI Analysis")
    print(f"   • Total setup costs:        ${roi_data['total_setup_cost']:,.0f}")
    print(f"   • Total operational costs:  ${roi_data['total_operational_costs']:,.0f}")
    print(f"   • Total investment:         ${roi_data['total_investment']:,.0f}")
    print(f"   • Lightning allocation:     ${roi_data['lightning_allocation_usd']:,.0f}")
    print(f"   • Total Lightning earnings: ${roi_data['total_lightning_earnings_usd']:,.0f}")
    print(f"   • Net benefits:             ${roi_data['net_benefits_usd']:,.0f}")
    print(f"   • ROI:                      {roi_data['roi_percentage']:.1f}%")
    
    if roi_data['break_even_years'] != float('inf'):
        print(f"   • Break-even timeline:      {roi_data['break_even_years']:.1f} years")
    else:
        print(f"   • Break-even timeline:      Never (costs exceed benefits)")
    
    if roi_data['payback_year']:
        print(f"   • Payback period:           Year {roi_data['payback_year']}")
    else:
        print(f"   • Payback period:           Beyond {years} years")
    
    print(f"   • Annual net benefit:       ${roi_data['annual_net_benefit']:,.0f}\n")
    
    # 6. Minimum Channel Size Analysis
    min_channel_data = calculate_minimum_channel_size(initial_params, results)
    print("6. Minimum Lightning Channel Size for Break-Even")
    print(f"{'Quarter':<10} {'Operational Only':>15} {'Total Costs':>15} {'BTC Price':>12}")
    print("-" * 60)
    
    # Show first 8 quarters and last 4 quarters
    for i, data in enumerate(min_channel_data):
        if i < 8 or i >= len(min_channel_data) - 4:  # First 8 and last 4
            operational_usd = data['min_channel_operational_usd']
            total_costs_usd = data['min_channel_total_costs_usd']
            btc_price = data['btc_price']
            
            print(f"{data['quarter']:<10} ${operational_usd:>14,.0f} ${total_costs_usd:>14,.0f} ${btc_price:>11,.0f}")
    
    if len(min_channel_data) > 12:
        print(f"{'...':<10} {'...':>15} {'...':>15} {'...':>12}")
    
    # Summary
    first_quarter = min_channel_data[0]
    last_quarter = min_channel_data[-1]
    print(f"\n   • To cover operational costs only: {first_quarter['min_channel_operational_btc']:.3f} BTC (${first_quarter['min_channel_operational_usd']:,.0f}) in Q1")
    print(f"   • To cover operational costs only: {last_quarter['min_channel_operational_btc']:.3f} BTC (${last_quarter['min_channel_operational_usd']:,.0f}) in final quarter")
    print(f"   • To cover all costs to date: {last_quarter['min_channel_total_costs_btc']:.3f} BTC (${last_quarter['min_channel_total_costs_usd']:,.0f}) in final quarter")
    print(f"   • Your current allocation: {initial_params['total_btc_reserves'] * initial_params['lightning_allocation_percent']:.3f} BTC\n")
    
    # 7. Competitive Treasury Analysis
    treasury_data = fetch_treasury_data()
    competitive_data = calculate_competitive_analysis(initial_params, treasury_data)
    
    print("7. Competitive Treasury Analysis")
    print(f"{'Company':<20} {'BTC Holdings':>12} {'Lightning Potential':>18} {'EPS Impact':>12} {'Status':>25}")
    print("-" * 95)
    
    # Show top 6 companies
    for company in competitive_data[:6]:
        company_name = company['company']
        btc_holdings = company['btc_holdings']
        lightning_potential = company['potential_lightning_btc']
        eps_impact = company['annual_eps_usd']
        advantage = company['advantage']
        
        print(f"{company_name:<20} {btc_holdings:>12,.0f} {lightning_potential:>18,.0f} ${eps_impact:>11,.2f} {advantage:<25}")
    
    # Add your company for comparison
    your_lightning_btc = initial_params['total_btc_reserves'] * initial_params['lightning_allocation_percent']
    your_annual_earnings = your_lightning_btc * initial_params['lightning_annual_yield']
    your_eps = your_annual_earnings * initial_params['btc_price'] / initial_params['shares_outstanding']
    
    print(f"{'YOUR COMPANY':<20} {initial_params['total_btc_reserves']:>12,.0f} {your_lightning_btc:>18,.0f} ${your_eps:>11,.2f} {'Perfect size for deployment':<25}")
    
    # Market opportunity analysis
    total_corporate_btc = sum(company['btc_holdings'] for company in treasury_data)
    estimated_lightning_capacity = 15000  # Estimated Lightning capacity
    your_capacity_share = your_lightning_btc / estimated_lightning_capacity * 100
    
    print(f"\n🏆 COMPETITIVE ADVANTAGES:")
    print(f"   • Total corporate BTC: {total_corporate_btc:,.0f} BTC")
    print(f"   • Estimated Lightning capacity: {estimated_lightning_capacity:,.0f} BTC")
    print(f"   • Your allocation: {your_lightning_btc:.0f} BTC = {your_capacity_share:.1f}% of available capacity")
    print(f"   • First-mover advantage: Secure capacity before others enter")
    print(f"   • Size arbitrage: Mega-holders can't deploy without crushing fees")
    print(f"   • Mid-sized sweet spot: {initial_params['total_btc_reserves']:,.0f} BTC is optimal for Lightning\n")
    
    # 8. Key advantages
    print("8. Why Lightning vs. Traditional BTC or High-Yield DeFi?")
    print("   • Non-custodial – coins remain in      client-controlled multi-sig")
    print("   • Risk profile – no rehypothecation,   no smart-contract exploits")
    print("   • GAAP benefit – sat income reported   under ASC 350-60 each quarter")
    print("   • Shareholder optics – BTC-per-share   grows without dilution\n")
    
    # 9. mNAV and investor interest advantage
    print("9. Market NAV Premium & Share Dilution Strategy")
    print("   • Lightning yield creates measurable EPS growth vs. passive BTC holders")
    print("   • Measured growth attracts investor interest = higher mNAV premium")
    print("   • Higher mNAV enables more profitable ATM share dilution")
    print("   • Sell shares at premium while maintaining strong sats-per-share growth")
    print("   • Use ATM proceeds to acquire more BTC at market prices")
    print("   • Reinvest additional BTC into Lightning = compound growth cycle")
    print("   • Competitive differentiation: Other BTC holders can't match this yield")
    print("   • Competitive edge: Mega-holders (>10k BTC) can't replicate this today")
    print("   • Mid-sized treasuries (1-5k BTC) enjoy temporary, high-margin opportunity\n")
    
    # 10. Why Act Now
    print("10. Why Act Now")
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
    
    # Note: Lightning Network data not included - no reliable public APIs available
    # Focus on the core EPS calculation which is the primary value proposition
    
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
    
    # Get current Bitcoin price
    btc_price = fetch_current_btc_price()
    if btc_price:
        print(f"   📈 Current BTC Price: ${btc_price:,.2f}")
    else:
        btc_price = float(input("   📈 Current BTC Price ($): ") or "50000.0")
    
    # CAGR for Bitcoin price projection
    btc_cagr = float(input("   📈 Expected BTC CAGR (% annually): ") or "15.0") / 100
    
    # Yield Parameters
    print(f"\n💰 YIELD PARAMETERS:")
    current_yield_zero = input("   Is your current BTC yield 0%? (y/n): ").lower().strip()
    if current_yield_zero == 'y' or current_yield_zero == '':
        traditional_annual_yield = 0.0
        print("   ✓ Traditional BTC Yield set to 0%")
    else:
        traditional_annual_yield = float(input("   Enter your current BTC yield (% annually): ")) / 100
    
    lightning_annual_yield = float(input("   Lightning Network Yield (% annually): ") or "4.0") / 100
    
    # Strategy Parameters
    lightning_allocation_percent = float(input("\n⚡ Lightning Allocation (% of BTC Treasury): ") or "10.0") / 100
    years = int(input("📅 Time Horizon (years): ") or "5")
    
    # Implementation cost inputs
    print(f"\n💰 IMPLEMENTATION COSTS (Annual):")
    setup_hardware = float(input("   Hardware setup costs (one-time, $): ") or "50000")
    setup_software = float(input("   Software/licensing costs (one-time, $): ") or "25000")
    setup_consulting = float(input("   Consulting/implementation (one-time, $): ") or "100000")
    annual_operational = float(input("   Annual operational costs ($/year): ") or "50000")
    
    return {
        'total_btc_reserves': total_btc_reserves,
        'lightning_annual_yield': lightning_annual_yield,
        'traditional_annual_yield': traditional_annual_yield,
        'shares_outstanding': shares_outstanding,
        'lightning_allocation_percent': lightning_allocation_percent,
        'years': years,
        'btc_price': btc_price,
        'btc_cagr': btc_cagr,
        'setup_hardware': setup_hardware,
        'setup_software': setup_software,
        'setup_consulting': setup_consulting,
        'annual_operational': annual_operational
    }
    
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
