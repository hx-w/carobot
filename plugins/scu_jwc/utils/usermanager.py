# -*- coding: utf-8 -*-

import hashlib

def password_encryption(password: str) -> str:
    hlmd5 = hashlib.md5()
    hlmd5.update(password.encode('utf-8'))
    return hlmd5.hexdigest()
