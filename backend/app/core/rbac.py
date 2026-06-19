"""Centralized RBAC dependency guards.

.. deprecated::
    This module is deprecated. Use ``app.core.permissions.require_permission``
    and ``get_scoped_team_ids_for`` instead. Retained for reference during
    the dynamic role access control migration.

Usage in routers:
    current_user: User = Depends(require_team_admin_or_above)
    current_user: User = Depends(require_finance_viewer_access)
    current_user: User = Depends(require_auditor_access)
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids)
"""
