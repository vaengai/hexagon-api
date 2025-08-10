import requests
import jwt
from jwt.exceptions import InvalidTokenError, DecodeError, InvalidSignatureError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from app.logging_config import logger
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64
import os

security = HTTPBearer()

# Environment-based configuration (more secure)
JWKS_URL = os.getenv(
    "CLERK_JWKS_URL",
    "https://pleased-hedgehog-10.clerk.accounts.dev/.well-known/jwks.json",
)
ALGORITHMS = ["RS256"]
AUDIENCE = os.getenv(
    "CLERK_PUBLISHABLE_KEY",
    "pk_test_cGxlYXNlZC1oZWRnZWhvZy0xMC5jbGVyay5hY2NvdW50cy5kZXYk",
)
ISSUER = os.getenv("CLERK_ISSUER", "https://pleased-hedgehog-10.clerk.accounts.dev")


@lru_cache()
def get_jwks():
    """Fetch and cache JWKS from Clerk"""
    try:
        response = requests.get(JWKS_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=503, detail="Authentication service unavailable"
        )


def rsa_key_from_jwk(jwk):
    """Convert JWK to RSA public key in PEM format"""
    try:
        # Decode base64url-encoded values
        n_bytes = base64.urlsafe_b64decode(jwk["n"] + "==")
        e_bytes = base64.urlsafe_b64decode(jwk["e"] + "==")

        # Convert to integers
        n_int = int.from_bytes(n_bytes, byteorder="big")
        e_int = int.from_bytes(e_bytes, byteorder="big")

        # Create RSA public key
        public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
        public_key = public_numbers.public_key()

        # Convert to PEM format for PyJWT
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem
    except Exception as e:
        logger.error(f"Failed to convert JWK to RSA key: {e}")
        raise HTTPException(status_code=401, detail="Invalid key format")


def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user payload"""
    try:
        # Get token header to find key ID
        headers = jwt.get_unverified_header(token.credentials)
        kid = headers.get("kid")

        if not kid:
            raise HTTPException(status_code=401, detail="Missing key ID in token")

        # Fetch JWKS and find matching key
        jwks = get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if not key:
            logger.warning(f"Public key not found for kid: {kid}")
            raise HTTPException(status_code=401, detail="Public key not found")

        # Convert JWK to PEM format
        public_key_pem = rsa_key_from_jwk(key)

        # For Clerk tokens, audience verification can be problematic
        # as Clerk doesn't always include the 'aud' claim or uses frontend URL
        audience_to_verify = None
        verification_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": False,  # Disable by default for Clerk
            "verify_iss": True,
        }

        # If you want to verify audience, uncomment and set the correct value:
        # audience_to_verify = "your-frontend-domain.com"  # or AUDIENCE
        # verification_options["verify_aud"] = True

        payload = jwt.decode(
            token.credentials,
            public_key_pem,
            algorithms=ALGORITHMS,
            audience=audience_to_verify,
            issuer=ISSUER,
            options=verification_options,
        )

        logger.info(f"Successfully authenticated user: {payload.get('sub', 'unknown')}")
        return payload

    except (InvalidTokenError, DecodeError, InvalidSignatureError) as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")
