import re


def email_validator(email):
   pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
   if re.match(pattern,email):
      return True
   return False

def password_validator(password):
    if len(password)<8:
        return False
    return True 

def sid_validator(sid):
    print(type(sid))
    if len(sid)!=7:
        return False
    return True
