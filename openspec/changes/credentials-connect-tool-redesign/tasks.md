# Tasks: Credentials — Connect Tool Redesign

## 1. Backend

- [x] 1.1 Add token validation step to `POST /api/v1/credentials` — call `validate_api_key()` before persist; return 422 on `ProviderValidationError`
- [x] 1.2 Implement `POST /api/v1/credentials/validate` endpoint (validate only, no persist)
- [x] 1.3 Remove `environment` from `CredentialCreateRequest` and `CredentialUpdateRequest` schemas
- [x] 1.4 Keep `environment` column in DB for backward compatibility; stop returning it in `CredentialResponse`
- [x] 1.5 Add `pull_interval_minutes` to credential create/update; wire collector sync schedule (60 = hourly, 1440 = daily)
- [x] 1.6 Reload collector scheduler after credential create/update

## 2. Frontend

- [x] 2.1 Rename "Add Credential" button to "Connect Tool" in `CredentialsPage.tsx`
- [x] 2.2 Rename slide-over title to "Connect Tool"
- [x] 2.3 Remove environment (Production / Sandbox) field from credential form and list
- [x] 2.4 Handle 422 response on form submit — show `detail` message inline under API key field
- [x] 2.5 Add `validateCredential` to `frontend/src/api/credentials.ts`
- [x] 2.6 Show "Connected successfully" on valid save (no plain-key reveal flow)
- [x] 2.7 Add sync schedule field (Hourly / Daily) on connect and edit forms; show Sync column in list

## 3. Tests

- [x] 3.1 Backend: valid token saves credential and sets pull interval on collector
- [x] 3.2 Backend: invalid token returns 422 with provider error message
- [x] 3.3 Backend: `/credentials/validate` returns 422 for bad token without persisting
