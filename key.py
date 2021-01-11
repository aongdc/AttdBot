"""
Generates key for bot usage authorisation and admin verification.
"""

import _._key as _key


def usage_code():
    f = _key.usage_code()
    return str(f)

def admin_code():
    f = _key.admin_code()
    return str(f)

if __name__ == '__main__':
    print(usage_code())
    print(admin_code())