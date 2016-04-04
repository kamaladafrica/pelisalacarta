from Crypto.Cipher import AES
from Crypto.Util import Counter
from cursor import Cursor


class File(object):
    def __init__(self, info, file_id, key, file ,client, folder_id=None):
        self._client = client
        self.folder_id = folder_id
        self.file_id = file_id
        self.cursor = None
        self.key = key
        self.file = file
        self.info= info
        self.name =  info["n"]
        self.size = file["s"]
        self.request=None
        self.k = self.key[0] ^ self.key[4] , self.key[1] ^ self.key[5] , self.key[2] ^ self.key[6], self.key[3] ^ self.key[7]
        self.iv = self.key[4:6] + (0, 0)
        self.initial_value = (((self.iv[0] << 32) + self.iv[1]) << 64)
        if not self.folder_id:
            self.url= self.file["g"]
        else:
            self.url = None

    def prepare_decoder(self,offset):
        initial_value = self.initial_value + int(offset/16)
        self.decryptor = AES.new(self._client.a32_to_str(self.k), AES.MODE_CTR, counter = Counter.new(128, initial_value = initial_value))
        #self.decryptor = aes.AESModeOfOperationCTR(f=self,key=self._client.a32_to_str(self.k),counter=aes.Counter(initial_value=initial_value))
        rest = offset - int(offset/16)*16
        if rest:
            self.decode(str(0)*rest)

    def create_cursor(self,offset):
        c =  Cursor(self)
        c.seek(offset)
        self.cursor = c
        return c

    def decode(self, data):
        return self.decryptor.decrypt(data)



