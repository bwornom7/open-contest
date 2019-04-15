from code.util import register
from code.util.db import User
from code.util.auth import generatePassword
import logging

def createUser(params, setHeader, user):
    newPassword = generatePassword()
    user = User(
        params["username"],
        newPassword,
        params["type"]
    )
    user.save()
    return newPassword

def deleteUser(params, setHeader, user):
    username = params["username"]
    user = User.getByName(username)
    user.delete()
    return "ok"

register.post("/createUser", "admin", createUser)
register.post("/deleteUser", "admin", deleteUser)
