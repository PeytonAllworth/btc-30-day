
# Example Dog class

# create a blueprint called dog
class Dog:   
# Inside the Dog class, create a special function that runs when you make a new Dog object.
# this function should accept self, name and breed
    def __init__(self, name, breed): # we will basically define what the dog is from here on out
# write a line that takes the name parameter and stores it as the dog's name
        self.name = name
        # do dogs breed
        self.breed = breed
# create a function that makes the dog bark
    def bark(self): # this is a method that makes the self do an action
        print(f"{self.name} the bull terrier says woof!")
# dog class is now complete and i need to make next line test it by creating a dog object making it bark
if __name__ == "__main__":
    my_dog = Dog("spinach", "bull terrier")
    my_dog.bark()