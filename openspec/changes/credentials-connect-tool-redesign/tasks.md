# Tasks: Credentials — Connect Tool Redesign

## 1. Backend

- [ ] 1.1 Add token validation step to `POST /api/v1/credentials` — call `validate_api_key()` before persist; return 422 on `ProviderValidationError`
- [ ] 1.2 Implement `POST /api/v1/credentials/validate` endpoint (validate only, no persist)
- [ ] 1.3 Remove `environment` from `CredentialCreateRequest` and `CredentialUpdateRequest` schemas
- [ ] 1.4 Keep `environment` column in DB for backward compatibility; stop returning it in `CredentialResponse`
- [ ] 1.5 Update OpenAPI spec: add `/credentials/validate`, remove `environment` from request schemas

## 2. Frontend

- [ ] 2.1 Rename "Add Credential" button to "Connect Tool" in `CredentialsPage.tsx`
- [ ] 2.2 Rename slide-over title to "Connect Tool"
- [ ] 2.3 Remove environment (Production / Sandbox) field from credential form
- [ ] 2.4 Handle 422 response on form submit — show `detail` message inline under API key field
- [ ] 2.5 Add `validateCredential` to `frontend/src/api/credentials.ts`
- [ ] 2.6 Optional: "Verify key" button that calls `/credentials/validate` before full save

## 3. Tests

- [ ] 3.1 Backend: valid token saves credential and returns 201
- [ ] 3.2 Backend: invalid token returns 422 with provider error message
- [ ] 3.3 Backend: `/credentials/validate` returns 422 for bad token without persisting
- [ ] 3.4 Frontend: submit with bad key shows inline error, slide-over stays open
