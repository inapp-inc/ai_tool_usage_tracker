"""Parse provider member payloads into canonical ProviderMember rows."""

from app.collector.adapters.base import ProviderMember


def dedupe_members(members: list[ProviderMember]) -> list[ProviderMember]:
    seen: set[str] = set()
    unique: list[ProviderMember] = []
    for member in members:
        email = member.email.strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        unique.append(
            ProviderMember(
                email=member.email.strip(),
                name=member.name.strip() if member.name else None,
            )
        )
    unique.sort(key=lambda row: row.email.lower())
    return unique


def parse_cursor_members(payload: object) -> list[ProviderMember]:
    if not isinstance(payload, dict):
        return []
    members: list[ProviderMember] = []
    for row in payload.get("teamMembers", []):
        if not isinstance(row, dict):
            continue
        if row.get("isRemoved") is True:
            continue
        email = row.get("email")
        if not isinstance(email, str) or not email.strip():
            continue
        name = row.get("name")
        members.append(
            ProviderMember(
                email=email.strip(),
                name=name.strip() if isinstance(name, str) and name.strip() else None,
            )
        )
    return dedupe_members(members)


def parse_openai_org_users(payload: object) -> list[ProviderMember]:
    if not isinstance(payload, dict):
        return []
    members: list[ProviderMember] = []
    for row in payload.get("data", []):
        if not isinstance(row, dict):
            continue
        email = row.get("email")
        if not isinstance(email, str) or not email.strip():
            continue
        name = row.get("name")
        members.append(
            ProviderMember(
                email=email.strip(),
                name=name.strip() if isinstance(name, str) and name.strip() else None,
            )
        )
    return dedupe_members(members)


def parse_generic_members(payload: object) -> list[ProviderMember]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = (
            payload.get("members")
            or payload.get("data")
            or payload.get("teamMembers")
            or payload.get("users")
            or []
        )
    else:
        return []

    if not isinstance(rows, list):
        return []

    members: list[ProviderMember] = []
    for row in rows:
        if isinstance(row, str) and row.strip():
            members.append(ProviderMember(email=row.strip()))
            continue
        if not isinstance(row, dict):
            continue
        email = row.get("email") or row.get("userEmail") or row.get("user_email")
        if not isinstance(email, str) or not email.strip():
            continue
        name = row.get("name")
        members.append(
            ProviderMember(
                email=email.strip(),
                name=name.strip() if isinstance(name, str) and name.strip() else None,
            )
        )
    return dedupe_members(members)
