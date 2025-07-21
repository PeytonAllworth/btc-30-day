# 1. Import the requests library so we can fetch data from the mempool.space API.
import requests

# 2. Send a GET request to "https://mempool.space/api/mempool/recent" and store the response.
response = requests.get("https://mempool.space/api/mempool/recent")

# print(data[0]) // here ive commented out this checkpoint because it will be in the way with future steps :)

# 3. Convert the response to JSON (it will become a Python list of transaction dictionaries).
data = response.json() #the reason for starting with data is because the response is a json object and we want to convert it to a python dictionary so basically we are grabbing the "response" and making it work as a python dictionary

# print(data[0]) // here ive commented out this checkpoint because it will be in the way with future steps :)


# 4. Create an empty dictionary called fees = {} to store txid: fee pairs.
fees = {} # This is like creating an empty ledger where you’ll record txid: fee pairs.

# To fill this dictionary, we need to loop through the first 5 transactions in data:
for tx in data[:5]:
    fees[tx['txid']] = tx['fee'] # This is like writing a transaction (txid) and its fee (fee) in the ledger.

print(fees) # checkpoint 2 



# 5. Loop through only the first 5 transactions in the data (hint: use data[:5]).
#    Inside the loop, map each txid (tx['txid']) to its fee (tx['fee']).

# 6. Print the dictionary to check it looks right.

# 7. Use a for loop (for txid, fee in fees.items()) to print:
#    "Transaction [txid]: [fee] sat/vB" for each entry.


# Definitions 
# request library: helps python know we will fetch information from the web
# json: a json object is a data structure that stores key-value pairs—like a real-world address book or a Bitcoin ledger.
# list: An ordered sequence ([800000, 799999, 799998]). You find things by position (index).