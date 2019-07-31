import yaml
from passlib.hash import argon2
from .base import User


class YamlAuthStorage:
    def __init__(self, filename):
        with open(filename) as f:
            data = yaml.safe_load(f)
        self.users = {}
        for item in data:
            self.users[item["username"]] = User(**item)

    def check_login(self, username, password):
        user = self.users.get(username)
        if user and argon2.verify(password, user.password):
            return user
