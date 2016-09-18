import os
import binascii


def generate_token():
    return binascii.b2a_hex(os.urandom(16))
