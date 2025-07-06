import requests

url = "https://mempool.space/api/mempool"
response = requests.get(url)

print("Status Code:", response.status_code)
print(response.json())



