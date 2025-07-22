# practicing what i did in first latest_block.py on memory and then playing with new requests  

import requests

# Part 1: Get latest block height
response = requests.get("https://blockchain.info/latestblock")
latest_data = response.json()
latest_height = latest_data["height"]
print("Latest block height:", latest_height)

# Part 1.5: Get current block fees
print(f"\n--- Current Block #{latest_height} Analysis ---")
response = requests.get(f"https://blockchain.info/block-height/{latest_height}?format=json")
current_block_data = response.json()
current_block = current_block_data['blocks'][0]

# Calculate total fees from current block (skip coinbase transaction)
current_total_fees = 0
for tx in current_block['tx'][1:]:  # Skip the first transaction since it is the coinbase
    # Each transaction has an input and output value
    # Fee = sum of inputs - sum of outputs
    input_value = sum(input_tx['prev_out']['value'] for input_tx in tx['inputs'])
    output_value = sum(output['value'] for output in tx['out'])
    tx_fee = input_value - output_value
    current_total_fees += tx_fee

print(f"Current Block Height: {latest_height}")
print(f"Current Block Fees: {current_total_fees:,} satoshis ({current_total_fees/100_000_000:.8f} BTC)")

# playing around printing the total reward(not counting the coinbase) for the last halving event block


response = requests.get("https://blockchain.info/block-height/840000?format=json")
data = response.json()

# Get the first block (since block-height endpoint returns an array)
block = data['blocks'][0]

# Extract block height
block_height = block['height']

# Calculate total fees from all transactions but remeber to skip coinbase transaction
total_fees = 0
for tx in block['tx'][1:]:  # Skip the first transaction since it is the coinbase! mistake made and fixed.
    # Each transaction has an input and output value
    # Fee = sum of inputs - sum of outputs
    input_value = sum(input_tx['prev_out']['value'] for input_tx in tx['inputs'])
    output_value = sum(output['value'] for output in tx['out'])
    tx_fee = input_value - output_value
    total_fees += tx_fee

print(f"Block Height: {block_height}")
print(f"Total Fees: {total_fees} satoshis")
# after adjusting some mistakes I now see that the total fees are in line with published data on memepool.space confirming my code wokred!







# Calculate the complete reward breakdown
block_reward_btc = 3.125  # 4th halving block reward
block_reward_sats = block_reward_btc * 100_000_000  # Convert BTC to satoshis
total_reward_sats = block_reward_sats + total_fees
total_reward_btc = total_reward_sats / 100_000_000  # Convert back to BTC

print(f"\n4th halving block #{block_height} gave a reward of {block_reward_btc} BTC plus fees of {total_fees:,} satoshis ({total_fees/100_000_000:.8f} BTC) totalling {total_reward_btc:.8f} BTC!")

# Compare fee rates between current block and 4th halving block
print(f"\n--- Fee Rate Comparison ---")
print(f"Current Block #{latest_height}: {current_total_fees:,} satoshis")
print(f"4th Halving Block #{block_height}: {total_fees:,} satoshis")

if current_total_fees > total_fees:
    difference = current_total_fees - total_fees
    percentage = (current_total_fees / total_fees) * 100
    print(f"\n🔥 Current block fees are {difference:,} satoshis HIGHER than the 4th halving block!")
    print(f"📈 Current fees are {percentage:.1f}% of the 4th halving block fees!")
elif current_total_fees < total_fees:
    difference = total_fees - current_total_fees
    percentage = (current_total_fees / total_fees) * 100
    print(f"\n:( :( :( :( Current block fees are {difference:,} satoshis LOWER than the 4th halving block!")
    print("--------------------------------")
    if percentage < 1:
        print(f"📉 Current fees are {percentage:.4f}% of the 4th halving block fees!")
    else:
        print(f"📉 Current fees are {percentage:.1f}% of the 4th halving block fees!")
else:
    print(f"\n⚖️ Current block fees are EQUAL to the 4th halving block!")

print(f"\n🤔 Imagine what the block space demand and fees paid for halving 6 will be when we have the first block that is both a difficulty adjustment and halving; coinciding at block height 1,260,000!")

