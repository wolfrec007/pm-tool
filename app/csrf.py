from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel


class CsrfSettings(BaseModel):
    secret_key: str = "change-me-csrf-secret-in-production"
    cookie_samesite: str = "lax"
    cookie_secure: bool = False  # set True in production over HTTPS


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()
