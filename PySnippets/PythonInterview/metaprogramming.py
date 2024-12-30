class Animal:
    def voice(self):
        pass
  
    @classmethod
    def from_classname(self, classname):
        """We need to implement this method"""
        pass
  
class Cat(Animal):
    def voice(self):
        print("meow")
    
class Dog(Animal):
    def voice(self):
        print("bark")

# Example
cat = Animal.from_classname("Cat")
dog = Animal.from_classname("Dog")

