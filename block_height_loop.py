# Block Height Monitor (Day 10)
# This script basically checks the latest Bitcoin block height every 10 seconds.
# It uses a simple loop with basic error handling.

import requests
import time  # first time using this library, but it is a simple way to add a delay to my loop.

while True:
    try:
        response = requests.get("https://mempool.space/api/blocks/tip/height")
        if response.status_code == 200:                                          # 200 is the code that just means the request is successful.
            height = int(response.text)
            print(f"Current block height: {height}")                              
        else:
            print(f"Error: Unexpected status code {response.status_code}")
    except Exception as e:        
        print(f"Error fetching block height: {e}")
    
    time.sleep(10)                                                              # apparently this does not need the internet but my computer can count the number of tics
                                                                                # inside the machine..."When electricity passes through quartz, it vibrates at a precise frequency (e.g., 32,768 times per second)."
                                                                                # this is not reliable if everyone has their own quartz clock hence the probablistic clock that is used in the blockchain.
