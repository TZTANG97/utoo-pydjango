import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from apps.payments.services.wx_settings import load_private_key_pem


def sign_native_display(appid: str, timestamp: int, nonce_str: str, code_url: str) -> str:
    signature_str = f"{appid}\n{timestamp}\n{nonce_str}\nprepay_id={code_url}\n"
    pem = load_private_key_pem()
    key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    sig = key.sign(signature_str.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode("ascii")
