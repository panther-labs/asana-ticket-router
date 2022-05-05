import base64


def b64_decode(b64: str) -> str:
    return base64.b64decode(b64).decode('ascii')
