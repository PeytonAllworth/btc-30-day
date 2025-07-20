import requests # helping python know we will fetch information from the web

response = requests.get("https://blockchain.info/latestblock") # this is the url 
data = response.json() # this is the data grabbed from the url... .json() converts it to a Python dictionary.
latest_height = data['height'] # this is the height of the latest block

blocks = [latest_height, latest_height - 1, latest_height - 2, latest_height - 3, latest_height - 4] # this is the list of blocks ill be fetching

print(blocks)




