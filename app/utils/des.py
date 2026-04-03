import binascii

from pyDes import des, CBC, PAD_PKCS5

# 默认密钥（仅用于开发环境，生产环境应从配置读取）
DEFAULT_KEY = 'pityspwd'


class Des(object):

    @staticmethod
    def get_key():
        """从配置文件获取密钥，失败时使用默认值（开发环境）"""
        try:
            from config import Config
            key = getattr(Config, 'PASSWORD_RESET_KEY', DEFAULT_KEY)
            return key if len(key) == 8 else DEFAULT_KEY
        except Exception:
            return DEFAULT_KEY

    @staticmethod
    def des_encrypt(s):
        """
        DES 加密
        :param s: 原始字符串
        :return: 加密后字符串，16进制
        """
        secret_key = Des.get_key()  # 从配置获取密钥
        iv = secret_key  # 偏移
        # secret_key:加密密钥，CBC:加密模式，iv:偏移, padmode:填充
        des_obj = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        # 返回为字节
        secret_bytes = des_obj.encrypt(s, padmode=PAD_PKCS5)
        # 返回为16进制
        return binascii.b2a_hex(secret_bytes).decode()

    @staticmethod
    def des_decrypt(s):
        """
        DES 解密
        :param s: 加密后的字符串，16进制
        :return:  解密后的字符串
        """
        secret_key = Des.get_key()
        iv = secret_key
        des_obj = des(secret_key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        decrypt_str = des_obj.decrypt(binascii.a2b_hex(s), padmode=PAD_PKCS5)
        return decrypt_str.decode()
