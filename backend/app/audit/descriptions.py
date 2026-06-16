"""Human-readable audit descriptions."""

from __future__ import annotations


def format_role_label(role: str | None) -> str:
    if not role:
        return "User"
    labels = {
        "super_admin": "Super Admin",
        "team_admin": "Team Admin",
        "finance_viewer": "Finance Viewer",
        "team_member": "Team Member",
        "auditor": "Auditor",
    }
    return labels.get(role, role.replace("_", " ").title())


def build_description(
    action: str,
    *,
    resource_name: str | None = None,
    extra: str | None = None,
) -> str:
    name = resource_name or "resource"
    templates: dict[str, str] = {
        "auth.login": "Signed in to the platform",
        "auth.logout": "Signed out of the platform",
        "user.invite": f"Invited user {name}",
        "user.remove": f"Removed user {name}",
        "user.role_change": f"Changed role for {name}",
        "team.create": f"Created team {name}",
        "team.update": f"Updated team {name}",
        "team.delete": f"Deleted team {name}",
        "tool.connect": f"Connected tool {name}",
        "tool.update": f"Updated tool {name}",
        "tool.delete": f"Deleted tool {name}",
        "credential.generate": f"Created credential {name}",
        "credential.update": f"Updated credential {name}",
        "credential.revoke": f"Revoked credential {name}",
        "alert.create": f"Created alert rule {name}",
        "alert.update": f"Updated alert rule {name}",
        "alert.delete": f"Deleted alert rule {name}",
        "upload.submit": f"Imported usage file {name}",
        "upload.delete": f"Deleted upload {name}",
        "report.generate": f"Generated report {name}",
        "report.delete": f"Deleted report {name}",
    }
    base = templates.get(action, f"{action.replace('.', ' ').title()} — {name}")
    if extra:
        return f"{base} ({extra})"
    return base


def target_type_label(resource_type: str) -> str:
    labels = {
        "auth": "Session",
        "user": "User",
        "team": "Team",
        "tool": "Tool",
        "credential": "Credential",
        "alert": "Alert",
        "upload": "Upload",
        "report": "Report",
    }
    return labels.get(resource_type, resource_type.title())
