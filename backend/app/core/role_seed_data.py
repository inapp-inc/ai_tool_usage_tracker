"""System role permission matrix — mirrors current rbac.py policy."""

from app.models.roles import VALID_RESOURCES

PermRow = tuple[bool, bool, bool]  # can_read, can_write, team_scoped


def _deny() -> PermRow:
    return (False, False, False)


def _read(team_scoped: bool = False) -> PermRow:
    return (True, False, team_scoped)


def _read_write(team_scoped: bool = False) -> PermRow:
    return (True, True, team_scoped)


def _full() -> PermRow:
    return (True, True, False)


def system_role_permissions(role_name: str) -> dict[str, PermRow]:
    """Return permission rows for a system role name."""
    deny = {resource: _deny() for resource in VALID_RESOURCES}

    if role_name == "super_admin":
        return {resource: _full() for resource in VALID_RESOURCES}

    if role_name == "team_admin":
        perms = deny.copy()
        perms.update(
            {
                "insights": _read(team_scoped=True),
                "alerts": _read_write(team_scoped=True),
                "uploads": _read_write(team_scoped=True),
                "members": _read_write(team_scoped=True),
                "tools": _read(),
                "teams": _read(),
                "collectors": _read(team_scoped=True),
                "my_usage": _read(),
            }
        )
        return perms

    if role_name == "finance_viewer":
        perms = deny.copy()
        perms["reports"] = _read()
        perms["my_usage"] = _read()
        return perms

    if role_name == "auditor":
        perms = deny.copy()
        perms["audit_logs"] = _read()
        perms["my_usage"] = _read()
        return perms

    if role_name == "team_member":
        perms = deny.copy()
        perms["my_usage"] = _read()
        return perms

    return deny
