import requests
import yfinance as yf

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

def main():
    print("=== MARA Miner Valuation Tool (Quick-Start) ===")
    btc_price = get_btc_price()
    market_cap = get_mara_market_cap()

    print(f"BTC Price: ${btc_price:,.0f}")
    print(f"MARA Market Cap: ${market_cap:,.0f}")

    # Placeholder for later:
    print("[A] Snapshot — TODO")
    print("[B] Normalized History — TODO")
    print("[C] Forward Projection — TODO")
    print("[D] Valuation — TODO")
    print("Action — TODO")

if __name__ == "__main__":
    main()
