# API Contract: GitOps Sync

This document defines the REST API contract for the manual Git synchronization trigger.

## `POST /api/git/sync`
Triggers an immediate synchronization of Python scripts from the remote Git repository into the target directory configured on the backend.

### Request
- **Method**: `POST`
- **URL**: `/api/git/sync`
- **Headers**:
  - `Authorization`: `Bearer <SYNC_SECRET>` (Required)
- **Body**: None required (uses backend environment variables).

### Response: Success
- **Status Code**: `200 OK`
- **Body**:
```json
{
  "status": "success",
  "message": "GitOps synchronization successful. Scripts rerendered."
}
```

### Response: Unauthorized
- **Status Code**: `401 Unauthorized`
- **Body**:
```json
{
  "detail": "Invalid or missing SYNC_SECRET bearer token."
}
```

### Response: General Error (E.g., Missing configuration)
- **Status Code**: `400 Bad Request`
- **Body**:
```json
{
  "detail": "Missing GitOps configuration: GIT_SSH_URL, GIT_SSH_KEY_PATH, or GIT_TARGET_PATH not set."
}
```

### Response: Authentication/Connection Error
- **Status Code**: `400 Bad Request` (or `503 Service Unavailable`)
- **Body**:
```json
{
  "detail": "Failed to connect to Git repository. Please verify your SSH credentials and network connectivity."
}
```

### Response: Validation Error (Malicious files)
- **Status Code**: `400 Bad Request`
- **Body**:
```json
{
  "detail": "Sync aborted: Detected non-.py or non-.txt files in the remote repository."
}
```

### Response: Syntax Error
- **Status Code**: `400 Bad Request`
- **Body**:
```json
{
  "detail": "Syntax error rendering updated scripts. Rollback performed. Details: SyntaxError on line 12 in store/my_dashboard.py"
}
```
