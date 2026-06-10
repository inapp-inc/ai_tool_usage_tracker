# Notification Center API — Delta Specification

## ADDED Requirements

### Requirement: List notifications for current user

The system SHALL implement `GET /api/v1/notifications` returning paginated notifications scoped to the authenticated user per FR-NTF-001.

#### Scenario: List includes unread count

- **GIVEN** a user with unread notifications
- **WHEN** `GET /notifications` is called
- **THEN** the response includes `data`, `unread_count`, and pagination `meta`
- **AND** each notification includes required OpenAPI fields including `deep_link`

#### Scenario: Unread only filter

- **GIVEN** read and unread notifications
- **WHEN** `GET /notifications?unread_only=true` is called
- **THEN** only unread items are returned

### Requirement: Unread notification count

The system SHALL implement `GET /api/v1/notifications/unread-count`.

#### Scenario: Unread count matches database

- **GIVEN** three unread notifications for the user
- **WHEN** unread-count endpoint is called
- **THEN** `unread_count` is 3

### Requirement: Mark notification as read

The system SHALL implement `POST /api/v1/notifications/{notificationId}/read`.

#### Scenario: Mark read decrements counter

- **GIVEN** an unread notification owned by the caller
- **WHEN** mark-read is posted
- **THEN** the notification `read` flag is true
- **AND** subsequent unread-count decreases by one

#### Scenario: Cross-user notification not found

- **GIVEN** a notification belonging to another user
- **WHEN** mark-read is attempted
- **THEN** the response status is 404 Not Found

### Requirement: RBAC notification visibility

The system SHALL only deliver notifications for events within the recipient's authorized scope.

#### Scenario: User does not see out-of-scope notifications

- **GIVEN** a threshold breach notification for team T
- **WHEN** a user without access to team T lists notifications
- **THEN** that notification is not included in their results
