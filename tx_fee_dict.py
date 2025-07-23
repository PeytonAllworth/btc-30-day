# Bitcoin Economics Notes
#
# In the Bitcoin network, a "vB" stands for "virtual byte," a unit of measurement for transaction size that accounts for SegWit (Segregated Witness) data.
# For miners, vB(where 1 vB = 4 weight units per BIP 141) is crucial because block space is limited, and they are incentivized to include transactions 
# that pay the highest fees per vB (sats/vB),
# SegWit discounts witness (signature) bytes to 1 weight unit (WU) each, while non witness bytes count as 4 WU each. 
# The total weight is divided by 4 to get the virtual size in vB, 
# so SegWit transactions can fit more data into the same block size limit.
# maximizing their revenue from transaction fees.
# For users, the sats/vB rate determines how quickly their transaction will be confirmed: higher sats/vB means faster confirmation due to incentive from miners,
# while lower sats/vB may result in longer wait times.
# This creates a fee market, where users compete for limited block space, especially during periods of high network activity.
# The variable sats/vB rates at similar times arise from this competition, users with urgent transactions bid higher,
# but also from technical features like Replace-by-Fee (RBF), Child-Pays-For-Parent (CPFP), 
# and wallet software targeting different confirmation speeds (an example is like with Strike... next block vs. within 6 blocks).
# while others may opt for lower fees and potentially may opt to wait longer.
# This dynamic pricing ensures block space is allocated efficiently, 
# reflecting real time demand and incentivizing miners to generally process the most valuable transactions.
# Miners can accept or deny transactions for other reasons be it political, or anything else, but will generally make decisions with economic incentives in mind.

# This dynamic creates a market for limited block space that will be one of the most important commodities in the future for financial data and likely more. 
# The "time-chain"(Satoshis original name for the blockchain) will also enable a time keeping mechanism for contracts that can use future block heights 
# to create time based contracts and sell futures for block space(I believe this on first principles of economics and what is technically possible).
# Block space as a commodity and futures as new financial instruments will mean that banks and other financial institutions will rely on Bitcoin
# miners to secure their data and transactions.
# The unit of account for this market will be in sats!
# Since the companies and individuals that will be securing and selling block space will be benefactors of Bitcoin's growth, and, as already seen with companies 
# like MARA, switching between selling energy to mine bitcoin, selling energy to the grid, and selling energy for AI compute,
# it is likely that the unit of account for the 3 most important commodities in the future(energy, block space, and compute for AI) WILL ALL BE IN SATS!

# deliverable block-space futures extend the hedging toolkit that already exists in the mining sector finance. This would take volatile sats/vB into a
# predictable cash-flow stream for miners a timing hedge (or tradeable
# asset) for any institution that relies on on-chain settlement. Allowing them to hedge against volatility in the sats/vB market.
# The first mining companies that can succesfully sell block-space futures will be the ones that are able to hedge against volatility in the sats/vB market
# and finance growth to increase their market share.
# This is a win-win for everyone involved, miners get a predictable cash-flow stream, institutions get a timing hedge, 
# and the market for block space as a commodity and futures as new financial instruments will grow.




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






