# coding: utf-8
"""
@Author：Robby
@ModuleName: encrypt_decrypt
@CreateTime: 2019-11-11
@模块功能: 对密码加密和解密
"""
from Crypto.Cipher import AES
from Crypto import Random
from binascii import b2a_hex, a2b_hex


SECRET_KEY = '%dt2248fw%gjmbelt7c1*uxz2izztfj72ko)umo3af$58+0a+*'

# 加密
def encrypt(data: str):
    """
    :param data: 对data进行AES加密
    :return: 返回加密字符串
    """
    text = data
    vector = Random.new().read(AES.block_size)
    key = SECRET_KEY[4:20].encode()
    cipher = AES.new(key, AES.MODE_CFB, vector)
    tmp = vector + cipher.encrypt(text.encode())
    cipher_text_bytes = b2a_hex(tmp)
    cipher_text = cipher_text_bytes.decode()
    return cipher_text


# 解密
def decrypt(data: str):
    """
    :param data: 对data进行AES解密
    :return: 返回解密字符串
    """
    text = data
    key = SECRET_KEY[4:20].encode()
    bytes_text = text.encode()
    cipher_text = a2b_hex(bytes_text)
    vector = cipher_text[:16]
    cipher = AES.new(key, AES.MODE_CFB, vector)
    decrypt = cipher_text[16:]
    decrypt_text = cipher.decrypt(decrypt)
    decrypt_text_str = decrypt_text.decode()
    return decrypt_text_str


if __name__ == '__main__':
    raw_data = "zHAs3erVUnD0DkJz"
    # raw_data = '7ozysja49fn5k81#5w_)pn9e6%)uma(&*rz_zv^oye5^lvp4^1'
    print(raw_data)
    cipher_data = encrypt(raw_data)
    print(cipher_data)
    data = decrypt(cipher_data)
    print(data)