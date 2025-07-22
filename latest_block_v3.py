import requests


def get_latest_block():
    try:
        response = requests.get("https://blockchain.info/latestblock", timeout=10)
        response.raise_for_status()  # Raises error if bad response
        latest_data = response.json()
        latest_height = latest_data["height"]
        return latest_height
    except Exception as e:
        print("Sorry, error fetching latest block:", e)
        return None

height = get_latest_block()
print(f"Latest block height: {height}")







   

