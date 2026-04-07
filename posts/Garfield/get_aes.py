from impacket.krb5.crypto import string_to_key

password = 'GoldenTicketKey2026!@#'
salt = 'GARFIELD.HTBkrbtgt_8245'

# string_to_key returns a Key object. The raw bytes are stored in .contents
key_object = string_to_key(18, password, salt)

print(f"AES256 Key: {key_object.contents.hex()}")
