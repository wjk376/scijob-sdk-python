from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

_RSA_PUBLIC_KEY = RSA.import_key("""
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvUnEHOE/RSFqjJkLhZMO
veh5KF8LmASaDFYqQT0/DOfITfoYmu4Fdf4rrmXvTqpL3ljISjP0LOXK0w93Wtpd
z0OjoH+sX4jE++B75qvfaZtKoRfmeJD7TZxZqgwhRTHAqKCKrXvlq18H/icJo2Az
5AJuSLUL9WRHSa+kOcSZHDsjsxndr9bVoTCzFiIny0GrNgs7JizneQieQuUSvfMH
rqhupUJS65zoXlYhL/Tbiy/hSvt9whRvB3Kv6/duaiEPcyJHZ/R/3P/lm473R7mE
oF5rbCd+pt3s8IGIGNvDFBeipSG+31CSU3AthvyM0VMXkQLjJSQDVKklpBlDj7hn
JwIDAQAB
-----END PUBLIC KEY-----
""".strip())


def rsa_encrypt(message: str, label: bytes = b""):
    cipher = PKCS1_OAEP.new(key=_RSA_PUBLIC_KEY, hashAlgo=SHA256, label=label)
    return cipher.encrypt(message.encode()).hex()