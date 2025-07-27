# yieldmodel.py
# A simple Bitcoin yield growth calculator.

def simulate_yield(initial_btc, btc_price, annual_yield, years):
    monthly_yield = annual_yield / 12
    btc_balance = initial_btc
    results = []

    for month in range(1, years * 12 + 1):
        btc_balance *= (1 + monthly_yield)
        usd_value = btc_balance * btc_price
        results.append((month, btc_balance, usd_value))

    return results

if __name__ == "__main__":
    # ---- EDIT THESE VALUES ----
    initial_btc = 0.5        # Starting BTC amount
    btc_price = 60000        # BTC price in USD
    annual_yield = 0.05      # Annual yield (5% = 0.05)
    years = 3                # Number of years to project
    # ---------------------------

    data = simulate_yield(initial_btc, btc_price, annual_yield, years)

    print("\n--- Bitcoin Yield Projection ---")
    print(f"Initial BTC: {initial_btc} BTC (${initial_btc * btc_price:,.2f})")
    print(f"Annual Yield: {annual_yield * 100:.2f}%")
    print(f"Time Horizon: {years} years\n")
    print(f"{'Month':<6} {'BTC Balance':<15} {'USD Value':<15}")

    for month, btc, usd in data:
        print(f"{month:<6} {btc:<15.8f} ${usd:<15,.2f}")

    final_btc = data[-1][1]
    final_usd = data[-1][2]
    print(f"\nFinal Balance after {years} years: {final_btc:.8f} BTC (${final_usd:,.2f})")
