from fastapi import Request


def set_flash(request: Request, message: str, level: str = "success"):
    """Set a flash message in the session. level: success, danger, warning, info."""
    request.session["_flash"] = {"message": message, "level": level}


def pop_flash(request: Request) -> dict | None:
    """Retrieve and clear the flash message from the session."""
    return request.session.pop("_flash", None)


def get_flash_context(request: Request) -> dict:
    """Get flash message for template context (reads but doesn't clear — cleared on next request via middleware)."""
    flash = request.session.get("_flash")
    if flash:
        return {"flash_message": flash["message"], "flash_level": flash["level"]}
    return {}
