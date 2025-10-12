# backend_common/jwt_tools.py
import os, time, jwt
from typing import Dict, Any

ALG = "HS256"

def _now() -> int:
    return int(time.time())

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default

def make_token(payload: Dict[str, Any], *, ttl_seconds: int) -> str:
    secret = os.getenv("JWT_SECRET", "dev-secret-change-me")
    iss = os.getenv("JWT_ISSUER", "mealapp-api")
    aud = os.getenv("JWT_AUDIENCE", "mealapp-client")
    iat = _now()
    exp = iat + ttl_seconds
    claims = {**payload, "iss": iss, "aud": aud, "iat": iat, "exp": exp}
    return jwt.encode(claims, secret, algorithm=ALG)

def verify_token(token: str) -> Dict[str, Any]:
    secret = os.getenv("JWT_SECRET", "dev-secret-change-me")
    iss = os.getenv("JWT_ISSUER", "mealapp-api")
    aud = os.getenv("JWT_AUDIENCE", "mealapp-client")
    return jwt.decode(token, secret, algorithms=[ALG], audience=aud, issuer=iss)

def mint_access_and_refresh(user: Dict[str, Any]) -> Dict[str, str]:
    """Generate short-lived access + longer refresh tokens."""
    access_ttl = _env_int("JWT_ACCESS_TTL_MIN", 15) * 60
    refresh_ttl = _env_int("JWT_REFRESH_TTL_DAYS", 7) * 86400
    sub = str(user["_id"])
    roles = user.get("roles", [])
    base = {"sub": sub, "email": user["email"], "roles": roles}
    access_token  = make_token({**base, "typ": "access"},  ttl_seconds=access_ttl)
    refresh_token = make_token({**base, "typ": "refresh"}, ttl_seconds=refresh_ttl)
    return {"access_token": access_token, "refresh_token": refresh_token}
