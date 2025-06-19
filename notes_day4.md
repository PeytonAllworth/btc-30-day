# Day 4: Loops in Python

# For Loops
Used when the number of repetitions is known. Great for iterating over ranges or collections.

```python
for i in range(5):
    print(i)

txids = ["tx123abc", "tx456def", "tx789ghi"]
for txid in txids:
    print(txid)
    
    
    
    
     While Loops

Used when the loop should run until a condition is met. Perfect for countdowns or input validation.

count = 5
while count > 0:
    print(count)
    count -= 1
✅ Input Validation with While

Repeat until valid input is received.

while True:
    number = int(input("Enter a number divisible by 21: "))
    if number % 21 == 0:
        print("Nice!")
        break
    else:
        print("Try again.")
🎨 Styled Countdown Using Dictionary

A cleaner way to manage output formatting based on loop state.


# i didnt use style map but this could be a cleaner way to go about things
style_map = {
    5: "...",
    4: "..",
    3: ".",
    2: "..",
    1: "..."
}
count = 5
while count > 0:
    print(f"{count}{style_map[count]}")
    count -= 1
🧠 Concepts Practiced

For vs while loops
range() and list iteration
break and if conditions
Input casting and validation
f-strings and dictionary lookups