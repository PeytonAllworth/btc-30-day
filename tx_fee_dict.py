# 1. Import the requests library so we can fetch data from the mempool.space API.
import requests

# 2. Send a GET request to "https://mempool.space/api/mempool/recent" and store the response.
response = requests.get("https://mempool.space/api/mempool/recent")
data = response.json()  #the reason for starting with data is because the response is a json object and we want to convert it to a python dictionary so basically we are grabbing the "response" and making it work as a python dictionary
print(data)

# 3. Convert the response to JSON (it will become a Python list of transaction dictionaries).

# 4. Create an empty dictionary called fees = {} to store txid: fee pairs.

# 5. Loop through only the first 5 transactions in the data (hint: use data[:5]).
#    Inside the loop, map each txid (tx['txid']) to its fee (tx['fee']).

# 6. Print the dictionary to check it looks right.

# 7. Use a for loop (for txid, fee in fees.items()) to print:
#    "Transaction [txid]: [fee] sat/vB" for each entry.


# Definitions 
# request library: helps python know we will fetch information from the web
# python dictionary: a python dictionary is a data structure that stores key-value pairs—like a real-world address book or a Bitcoin ledger.
# list: An ordered sequence ([800000, 799999, 799998]). You find things by position (index).