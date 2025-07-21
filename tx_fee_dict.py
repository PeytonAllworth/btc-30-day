# Bitcoin Notes
#
# In the Bitcoin network, a "vB" stands for "virtual byte," a unit of measurement for transaction size that accounts for SegWit (Segregated Witness) data.
# For miners, vB is crucial because block space is limited, and they are incentivized to include transactions that pay the highest fees per vB (sat/vB), maximizing their revenue from transaction fees.
# For users, the sat/vB rate determines how quickly their transaction will be confirmed: higher sat/vB means faster confirmation, while lower sat/vB may result in longer wait times.
# This creates a fee market, where users compete for limited block space, especially during periods of high network activity.
# The variable sat/vB rates at similar times arise from this competition—users with urgent transactions bid higher, while others may opt for lower fees and wait longer.
# This dynamic pricing ensures block space is allocated efficiently, reflecting real-time demand and incentivizing miners to process the most valuable transactions.

# This dynamic creates a market for limited block space that will be one of the most important commodities in the future for financial data and more. 
# The "time-chain" will also enable a time keeping mechanism for contracts that can use future block heights to create time based contracts and sell futures for block space.
# Block space as a commodity and futures as new financial instruments will mean that banks and other financial institutions will rely on Bitcoin mining pools to secure their data and transactions.
# The unit account for this market will be in sats!

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
    fee_rate = tx['fee'] / tx['vsize']
    fees[tx['txid']] = fee_rate

#print(fees) # checkpoint 2 

# 7. Use a for loop (for txid, fee in fees.items()) to print:
#    "Transaction [txid]: [fee] sat/vB" for each entry.

print("Recent Bitcoin Transactions and Their Fees")
print("-" * 50)

for txid, fee_rate in fees.items():
    # Find the transaction in data to get its vsize
    tx = next((tx for tx in data[:5] if tx['txid'] == txid), None)
    if tx:
        fee_rate = tx['fee'] / tx['vsize']
        print(f"Transaction {txid}: {fee_rate:.2f} sat/vB")




# Definitions 
# request library: helps python know we will fetch information from the web
# json: a json object is a data structure that stores key-value pairs—like a real-world address book or a Bitcoin ledger.
# list: An ordered sequence ([800000, 799999, 799998]). You find things by position (index).






