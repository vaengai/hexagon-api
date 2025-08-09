import requests
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from app.logging_config import logger
import json
from cryptography.hazmat.primitives import serialization

security = HTTPBearer()

JWKS_URL = "https://pleased-hedgehog-10.clerk.accounts.dev/.well-known/jwks.json"
ALGORITHMS = ["RS256"]
AUDIENCE = (
    "pk_test_cGxlYXNlZC1oZWRnZWhvZy0xMC5jbGVyay5hY2NvdW50cy5kZXYk"  # Or your app URL
)
ISSUER = "https://pleased-hedgehog-10.clerk.accounts.dev"


@lru_cache()
def get_jwks():
    return requests.get(JWKS_URL).json()


def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        headers = jwt.get_unverified_header(token.credentials)
        jwks = get_jwks()

        key = next((k for k in jwks["keys"] if k["kid"] == headers["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found")

        public_key = {
            "kty": key["kty"],
            "kid": key["kid"],
            "use": key["use"],
            "n": key["n"],
            "e": key["e"],
        }

        payload = jwt.decode(
            token.credentials,
            public_key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
            issuer=ISSUER,
        )

        return payload
    except JWTError as e:
        logger.error(f"Token verification failed. Reason:{e}")
        raise HTTPException(status_code=401, detail="Token verification failed")
