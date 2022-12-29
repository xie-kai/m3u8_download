from Crypto.Cipher import AES


class DataParse:

    def __init__(self, key, iv=None, mode=AES.MODE_CBC, pad=b"\0"):
        self.iv  = iv
        self.key = key
        self.pad = pad
        self.mode = mode
        self._create_cipher()

    def _create_cipher(self, **kwargs):
        kwargs = self._initialization(**kwargs)
        self.cipher = AES.new(**kwargs)

    def _initialization(self, **kwargs):
        kwargs["key"] = kwargs.get("key", self.key)
        kwargs["iv"]  = kwargs.get("iv", self.iv)
        if not kwargs["iv"]:
            kwargs.pop("iv")
        else:
            kwargs["iv"] = kwargs["iv"].replace("0x", "", 1).encode() \
                               if isinstance(kwargs["iv"], str) else kwargs["iv"]
            kwargs["iv"] = kwargs["iv"][:AES.block_size]
        kwargs["mode"] = kwargs.get("mode", self.mode)
        for key, val in kwargs.copy().items():
            if isinstance(val, str):
                kwargs[key] = val.encode()
        return kwargs


class AESEncryption(DataParse):

    def decrypt(self, ciphertext):
        # 解密
        ciphertext = self._padding(ciphertext)
        self._create_cipher()
        return self.cipher.decrypt(ciphertext).rstrip(self.pad)

    def encrypt(self, plaintext):
        # 加密
        plaintext = self._padding(plaintext)
        self._create_cipher()
        return self.cipher.encrypt(plaintext)

    def _padding(self, content):
        # 填充至16倍数
        if not isinstance(content, bytes):
            raise TypeError(f"加密或解密数据类型必需bytes! Error Type: {type(content)}")
        remainder = len(content) % AES.block_size
        if remainder:
            content += (AES.block_size - remainder) * self.pad
        return content
