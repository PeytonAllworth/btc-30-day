# 1. String Variables and Interpolation

# Define name and project
name = "Peyton"
project = "Bitcoin CLI sprint"
# Print: "Peyton is crushing Day 3 of the Bitcoin CLI sprint!"
print(name + " is crushing Day 3 of the " + project + "!")
print(f"{name} is crushing Day 3 of the {project}!") #trying both
# Bonus: Try it with + and with f-strings








# 2. Input + Type Casting




# Ask the user their age

age = input("how old are you ")

# Convert it to an integer

age = int(age)

# Print: "You'll be [age + 1] next year."

print(f"you'll be {age + 1} next year")

if age==31: 
    print("Drew is a coward")

# Bonus: What happens if they enter "ten" instead of 10? Try it.









# 3. Math and Variables

# Define BTC price and number of sats you own
btc_price = 105000 #im defining the value of a variable 
sats_owned = 210_000_000
btc_amount = sats_owned / 100_000_000
# Print how much your sats are worth in USD
fiat_value = btc_amount * btc_price
print(f"Your {sats_owned} sats are worth ${fiat_value:.2f} at ${btc_amount}/BTC")

# Bonus: Format to 2 decimal places
