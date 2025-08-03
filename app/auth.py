import os
from functools import lru_cache

import requests
from fastapi import HTTPException
from fastapi.params import Header
from jose import jwt, jwk, JWTError


@lru_cache()
def get_clerk_jwks():
    return requests.get(
        f"https://pleased-hedgehog-10.clerk.accounts.dev/.well-known/jwks.json",
        headers={"Authorization": f"Bearer {os.getenv('CLERK_API_KEY')}"},
    ).json()


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    header = jwt.get_unverified_header(token)
    jwks_data = get_clerk_jwks()
    key = next((k for k in jwks_data["keys"] if k["kid"] == header["kid"]), None)

    if not key:
        raise HTTPException(status_code=401, detail="Public key not found")

    try:
        public_key = jwk.construct(key)
        payload = jwt.decode(
            token,
            public_key.to_pem().decode("utf-8"),
            algorithms=["RS256"],
            audience=os.getenv("CLERK_FRONTEND_API")
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
