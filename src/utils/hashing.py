import bcrypt
import hashlib


class HashManager:
    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode(encoding="utf-8")
        hashed_pwd_bytes = bcrypt.hashpw(pwd_bytes, salt)
        return hashed_pwd_bytes.decode(encoding="utf-8")

    def _verify_password(
        self, password: str, hashed_password: str
    ) -> bool:
        return bcrypt.checkpw(
            password=password.encode(encoding="utf-8"),
            hashed_password=hashed_password.encode(
                encoding="utf-8"
            ),
        )

    def _hash_token(self, token: str) -> str:
        token_bytes = token.encode("utf-8")
        return hashlib.sha256(token_bytes).hexdigest()

    def _verify_token(self, token: str, hashed_token: str) -> bool:
        return self._hash_token(token) == hashed_token
