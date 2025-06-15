import requests
response = requests.get("https://blockchain.info/latestblock")
print(response.json())
print("Latest block height:", response.json()["height"])
print("Latest block height:", response.json()["height"])