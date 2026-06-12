# list_a = [1, 2, 3, "A", "B", "C"]

# array_a = [1, 2, 3, 4, 5]

# set_a = {1, 2, 3, 4, 5, 5}

# print(set_a)

# dict_a = {
#         "name": "Alice",
#         "age": 30,
#         "city": "New York",
#         "hobbies": ["reading", "traveling", "cooking"],
#         "name": "Bob"
#         }
#         # key: value

# dict_a = {}

# print(dict_a)

# # print(dict_a["hobbies"])

# dict_a["college"] = "Harvard"
# dict_a["college12"] = "Harvard"

# print(dict_a)


# def add_numbers(a, b):
#     return a + b

# result = add_numbers(5, 10)

# print(result)

# add = lambda a, b:a + b

# result = add(5, 10)
# print(result)

# def div_numbers(a, b):
#     """
#     This function takes two numbers as input and returns their quotient.
#     Parameters:
#     a (int or float): The first number.
#     b (int or float): The second number.

#     Returns:
#     int or float: The quotient of the two numbers.
#     """
#     return a / b

# try:
#     x = float(input('Enter number x: '))
#     y = float(input('Enter number y:'))
#     result = div_numbers(x, y)
#     print(result)
# except Exception as e:
#     print('An error occurred:', e)
#     print('Cannot divide by zero')

# finally:
#     print('This block will always execute')


#     except ValueError:
# print('Invalid input')



class Student:
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender

    def greet(self):
        print('Hi, I am', self.name, 'and I am', self.age, 'years old.')

    def whoami(self, college='Unknown'):
            print('Hi, I am', self.name, 'and I am from', college)

# p = Student('Bob', 25, 'Male')
# a = p.whoami()
# print("Class - Student - ", a)
     
class Student_Info(Student):
    def __init__(self, name, age, gender):
        super().__init__(name, age, gender)

    # def __init__(self, name, age, gender):
    #     self.name = name
    #     self.age = age
    #     self.gender = gender        

    def whoami(self, college='Unknown', location='Unknown'):
        print('Hi, I am', self.name, 'and I am from', college, 'and I live in', location)

c = Student_Info('Alice', 30, 'Female')
c.whoami()
c.greet()
