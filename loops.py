# Print "Bitcoin is freedom" 10 times using a for loop

for i in range(10) :
    print("Bitcoin is freedom")

# Countdown from 5 to 1, then say "Block mined!"
    count = 5
    while count > 0:
        if count == 5 or count == 1:
            print(f"{count}... ...")
        elif count == 4 or count == 2:
            print(f"{count}..   ..")
        else:
            print(f"{count}.     .")
        count -= 1
    print("Block mined!")




# Ask until the number entered is divisible by 21
while True: 
    number = int(input("enter a number that is divisible by 21: "))
    if number % 21 == 0:
        print("great job that is divisible by 21!")
        break
    else:
        print("not so good at math dude, try again.")

# Loop through fake Bitcoin transaction IDs and print them
txids = ["tx123aaa", "tx123aab", "tx123aac", "tx123aba", "tx123abb", "tx123abc", "tx123aca", "tx123acb", "tx123acc"]
for x in txids:
    print(f"processing the fake txid: {x}")
