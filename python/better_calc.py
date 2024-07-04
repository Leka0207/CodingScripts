import math

def add(x, y):
    return round(x + y, 4)

def subtract(x, y):
    return round(x - y, 4)

def multiply(x, y):
    return round(x * y, 4)

def divide(x, y):
    if y == 0:
        return "Error! Division by zero."
    return round(x / y, 4)

def exponentiate(x, y):
    return round(math.pow(x, y), 4)

def sqrt(x):
    if x < 0:
        return "Error! Square root of negative number."
    return round(math.sqrt(x), 4)

def log(x):
    if x <= 0:
        return "Error! Logarithm of non-positive number."
    return round(math.log(x), 4)

def calculator():
    print("Select operation:")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Exponentiate")
    print("6. Square Root")
    print("7. Logarithm")
    
    while True:
        choice = input("Enter choice(1/2/3/4/5/6/7): ")
        
        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            try:
                if choice == '6':
                    num1 = float(input("Enter the number: "))
                elif choice == '7':
                    num1 = float(input("Enter the number: "))
                else:
                    num1 = float(input("Enter first number: "))
                    num2 = float(input("Enter second number: "))
            except ValueError:
                print("Invalid input! Please enter numeric values.")
                continue
            
            if choice == '1':
                print(f"The result is: {add(num1, num2)}")
            elif choice == '2':
                print(f"The result is: {subtract(num1, num2)}")
            elif choice == '3':
                print(f"The result is: {multiply(num1, num2)}")
            elif choice == '4':
                print(f"The result is: {divide(num1, num2)}")
            elif choice == '5':
                print(f"The result is: {exponentiate(num1, num2)}")
            elif choice == '6':
                print(f"The result is: {sqrt(num1)}")
            elif choice == '7':
                print(f"The result is: {log(num1)}")
                
            next_calculation = input("Do you want to perform another calculation? (yes/no): ")
            if next_calculation.lower() != 'yes':
                break
        else:
            print("Invalid Input")

if __name__ == "__main__":
    calculator()
