from passlib.hash import argon2


def verify_password(password, password_hash):
    return argon2.verify(password, password_hash)


def hash_password(password):
    return argon2.hash(password)
