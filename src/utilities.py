def parse_lsp_config(filepath):
    stuid = ""
    pwd = ""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith("//"):
                continue
            if line.startswith("STUID="):
                stuid = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("PWD="):
                pwd = line.split("=", 1)[1].strip().strip('"')
    return stuid, pwd


from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
from config import LoginConfig
def encrypt_password(password: str) -> str:
    """
    使用AES-ECB模式加密密码
    :param password: 明文密码
    :return: Base64编码的加密结果
    """
    # 创建加密器实例
    cipher = AES.new(LoginConfig.AES_KEY, LoginConfig.AES_MODE)
    # 填充并加密数据
    padded_data = pad(password.encode(), LoginConfig.BLOCK_SIZE)
    encrypted = cipher.encrypt(padded_data)
    # 返回Base64字符串
    return base64.b64encode(encrypted).decode('utf-8')


