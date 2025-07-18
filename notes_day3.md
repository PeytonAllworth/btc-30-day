# Notes – Day 3 (CS50P: Variables)

## Key Concepts
- `input()` – Gets user input as a string
- `int()` – Converts string to integer
- `float()` – Converts string to decimal
- `str()` – Converts number to string
- `f""` – f-strings let you insert variables into strings
- Variables are names you give to store values
- Strings = text
- Integers = whole numbers
- Floats = numbers with decimals


# Notes – Day 3 (CS50P: Variables, Types, Input)

# Core Python Concepts

- **Variable**: A name pointing to a value
  - `x = 5`
  - Python is dynamically typed (you don’t declare `int x` like in other languages)

- **Input**: Gets a string from the user
  - `name = input("What is your name? ")`

- **Print**: Sends text to the screen
  - `print("hello, world")`
  - `print("hello, " + name)`
  - `print(f"hello, {name}")` ← f-strings are cleaner

- **Type Casting**:
  - `int()`: Converts string to integer
  - `float()`: Converts string to float
  - `str()`: Converts number to string

- **Errors**:
  - `ValueError`: Trying to cast `"ten"` with `int("ten")`
  - `NameError`: Using a variable that hasn’t been defined
  - Python is case-sensitive: `Name` ≠ `name`

- **Comments**:
  - `# This is a comment`
  - Good for describing your intent or skipping lines

- **Arithmetic Operators**:
  - `+` (add)
  - `-` (subtract)
  - `*` (multiply)
  - `/` (float division, e.g. 5 / 2 = 2.5)
  - `//` (integer division, e.g. 5 // 2 = 2)
  - `%` (modulus/remainder)
  - `**` (exponentiation)

- **Data Types**:
  - `int`: whole number
  - `float`: decimal
  - `str`: text
  - `bool`: `True` or `False`

- **Boolean Operators**:
  - `==` (equal)
  - `!=` (not equal)
  - `>` `<` `>=` `<=`

- **Type Checking**:
  - `type(variable)` shows the type of a variable

- **Escape Sequences**:
  - `\n` = new line
  - `\t` = tab

## 🧠 Quick Code Blocks:
```python
x = int(input("What's x? "))
y = int(input("What's y? "))
print(x + y)

z = x + y
print(f"{x} plus {y} is {z}")
