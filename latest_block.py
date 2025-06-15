import requests
height = requests.get("https://blockchain.info/q/getblockcount", timeout=10).text.strip()
print("Current Bitcoin block height:", height)
