from AesEverywhere import aes256
from django.conf import settings

import logging

_logger = logging.getLogger('django.AESCipher')

# from pythemis.skeygen import GenerateKeyPair, KEY_PAIR_TYPE
# from pythemis.smessage import SMessage
# from pythemis.exception import ThemisError

# server_keypair = GenerateKeyPair(KEY_PAIR_TYPE.EC)
# server_private_key = server_keypair.export_private_key()
# client_public_key = base64.b64decode('VUVDMgAAAC3ppgNuA3zW+TjNPBnDLvKteNrmvzXV2FXmJYRhLqm6A55+eL0Q')

# server_secure_message = SMessage(server_private_key, client_public_key)

# BS = 16
# KEY = hashlib.md5(settings.SECRET_KEY.encode('utf-8')).hexdigest()[:BS]
# pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
# unpad = lambda s : s[:-ord(s[len(s)-1:])]

class AESCipher:

    @staticmethod
    def encrypt(raw):
        return aes256.encrypt(raw, settings.API_SECRET_KEY)

    @staticmethod
    def decrypt(enc):
        return aes256.decrypt(enc, settings.API_SECRET_KEY)

    # def encrypt( self, raw ):
    #     raw = pad(raw)
    #     iv = Random.new().read( AES.block_size )
    #     cipher = AES.new( self.key, AES.MODE_CBC, iv )
    #     return base64.b64encode( iv + cipher.encrypt( raw ) )

    # def decrypt( self, enc ):
    #     enc = base64.b64decode(enc)
    #     iv = enc[:16]
    #     cipher = AES.new(self.key, AES.MODE_CBC, iv )
    #     return unpad(cipher.decrypt( enc[16:] ))

    # def encrypt( self, raw ):
    #     _logger.info("PLAIN TEXT : %s"%raw)
    #     encrypted_message = server_secure_message.wrap(raw)
    #     _logger.info("CIPHER TEXT : %s"%encrypted_message)
    #     return str(encrypted_message)

    # def decrypt( self, enc ):
    #     decrypted_message = ""
    #     try:
    #         _logger.info("CIPHER TEXT : %s"%enc)
    #         decrypted_message = server_secure_message.unwrap(enc.encode('utf-8'))
    #     # process decrypted data
    #     except ThemisError:
    #         pass
    #     _logger.info("PLAIN TEXT : %s"%decrypted_message)
    #     return decrypted_message
    #     # handle decryption failure

    # def encrypt(self,string):
    #     """
    #     It returns an encrypted string which can be decrypted just by the 
    #     password.
    #     """
    #     key = self.password_to_key()
    #     IV = self.make_initialization_vector()
    #     encryptor = AES.new(key, AES.MODE_CBC, IV)

    #     # store the IV at the beginning and encrypt
    #     return IV + encryptor.encrypt(self.pad_string(string))

    # def decrypt(self,string):
    #     key = self.password_to_key()

    #     # extract the IV from the beginning
    #     IV = string[:AES.block_size]  
    #     decryptor = AES.new(key, AES.MODE_CBC, IV)

    #     string = decryptor.decrypt(string[AES.block_size:])
    #     return self.unpad_string(string)

    # def password_to_key(self):
    #     """
    #     Use SHA-256 over our password to get a proper-sized AES key.
    #     This hashes our password into a 256 bit string. 
    #     """
    #     # return SHA256.new(password).digest()
    #     return KEY

    # def make_initialization_vector(self):
    #     """
    #     An initialization vector (IV) is a fixed-size input to a cryptographic
    #     primitive that is typically required to be random or pseudorandom.
    #     Randomization is crucial for encryption schemes to achieve semantic 
    #     security, a property whereby repeated usage of the scheme under the 
    #     same key does not allow an attacker to infer relationships 
    #     between segments of the encrypted message.
    #     """
    #     return Random.new().read(AES.block_size)

    # def pad_string(self,string, chunk_size=AES.block_size):
    #     """
    #     Pad string the peculirarity that uses the first byte
    #     is used to store how much padding is applied
    #     """
    #     assert chunk_size  <= 256, 'We are using one byte to represent padding'
    #     to_pad = (chunk_size - (len(string) + 1)) % chunk_size
    #     return bytes([to_pad]) + string + bytes([0] * to_pad)

    # def unpad_string(self,string):
    #     to_pad = string[0]
    #     return string[1:-to_pad]

    # def encode(self,string):
    #     """
    #     Base64 encoding schemes are commonly used when there is a need to encode 
    #     binary data that needs be stored and transferred over media that are 
    #     designed to deal with textual data.
    #     This is to ensure that the data remains intact without 
    #     modification during transport.
    #     """
    #     return base64.b64encode(string).decode("latin-1")

    # def decode(self,string):
    #     return base64.b64decode(string.encode("latin-1"))