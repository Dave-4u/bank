Username = input('Put in your username: ')

def Password_validator():
    global Confirm_Password
Password = input('Put in your password: ')
Confirm_Password = input('Confirm your password: ')
if Password == Confirm_Password:
    print('Sucessfully created account, login to dashboard')
    print("LOGIN PAGE")
    
else:
    print('Password and Confirm Password do not match please try again')
    Password_validator

def login():
    Username = input('Put in yout username: ')
    Password = input('Put in your password: ')
    if Password == Confirm_Password:
        print('Login Successful')
    else:
        print('Incorrect account details')



Password_validator()
print("LOGIN PAGE")  
login()      
