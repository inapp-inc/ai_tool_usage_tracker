"""Persist and read provider member lists on connected tool records."""

from app.collector.adapters.base import ProviderMember
from app.models.admin import Tool
from sqlalchemy.orm.attributes import flag_modified


def store_synced_members(tool: Tool, members: list[ProviderMember]) -> None:
    config = dict(tool.pricing_config) if isinstance(tool.pricing_config, dict) else {}
    config["synced_members"] = [
        {
            "email": member.email.strip(),
            "name": member.name.strip() if member.name else None,
        }
        for member in members
        if member.email and member.email.strip()
    ]
    tool.pricing_config = config
    flag_modified(tool, "pricing_config")
    tool.member_count = len(config["synced_members"])


def read_synced_members(tool: Tool) -> list[ProviderMember]:
    config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
    raw = config.get("synced_members")
    if not isinstance(raw, list):
        return []
    members: list[ProviderMember] = []
    for row in raw:
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
    return members
