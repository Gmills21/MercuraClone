# Security Hardening Audit Report

**Date:** 2026-02-13  
**Auditor:** R  
**Application:** OpenMercura CRM

---

## Executive Summary

A comprehensive security audit was performed on the OpenMercura CRM codebase following research on common video codec/processing application vulnerabilities. While the application doesn't process video codecs directly, the audit focused on file upload handling, authentication, authorization, and common web application vulnerabilities.

**Status:** All critical and high-severity issues have been remediated.

---

## Issues Found & Fixed

### 1. CORS Misconfiguration (CRITICAL)

**Issue:** CORS was configured to allow all origins (`["*"]`) with credentials enabled, allowing any website to make authenticated requests.

**Fix:** 
- Made CORS origins configurable via `CORS_ALLOWED_ORIGINS` environment variable
- Added production safety check - warns if `*` is used in production
- Restricted allowed methods and headers to minimum required
- Added `max_age` for preflight caching

**File:** `app/main.py`

---

### 2. Weak Password Hashing (CRITICAL)

**Issue:** Passwords were hashed using PBKDF2-SHA256 with only 100,000 iterations. This is below current OWASP recommendations (600,000+ iterations) and not memory-hard.

**Fix:**
- Implemented bcrypt as primary hashing algorithm with 12 rounds
- Added fallback to PBKDF2-SHA256 with 600,000 iterations if bcrypt unavailable
- Maintained backward compatibility with legacy password hashes
- Added automatic migration path for existing users

**File:** `app/auth.py`

---

### 3. Hardcoded Default Admin Password (CRITICAL)

**Issue:** Default admin user was created with hardcoded password `admin123` which is a critical security vulnerability.

**Fix:**
- Removed hardcoded password
- Default admin user now only created if `ADMIN_PASSWORD` environment variable is set
- Password is validated to be at least 12 characters on startup
- Added `ADMIN_EMAIL` environment variable support
- Logs warning if no users exist and no admin password is set

**File:** `app/database_sqlite.py`

---

### 4. Path Traversal via File Uploads (HIGH)

**Issue:** User-provided filenames were used without sanitization, potentially allowing path traversal attacks (e.g., `../../../etc/passwd`).

**Fix:**
- Created `app/security_utils.py` with `sanitize_filename()` function
- Sanitization removes null bytes, path separators, and dangerous characters
- Limits filename length to 255 characters
- Replaces invalid characters with underscores
- Applied sanitization to all file upload endpoints:
  - `/extract/` (extraction_unified.py)
  - `/image-extract/upload` (image_extract.py)
  - `/image-extract/base64` (image_extract.py)
  - `/knowledge/ingest` (knowledge_base.py)
  - `/inbound/*` (email_ingestion.py)

**Files:** 
- `app/security_utils.py` (new)
- `app/routes/extraction_unified.py`
- `app/routes/image_extract.py`
- `app/routes/knowledge_base.py`
- `app/routes/email_ingestion.py`

---

### 5. Missing Authorization on Backup Restore (HIGH)

**Issue:** Backup restore endpoint had a TODO comment for role checking but no actual implementation.

**Fix:**
- Added explicit admin role check before allowing restore
- Queries `organization_members` table to verify user role
- Returns 403 Forbidden for non-admin users

**File:** `app/routes/backups.py`

---

### 6. Backup ID Path Traversal (MEDIUM)

**Issue:** Backup IDs were accepted without validation, potentially allowing path traversal in backup operations.

**Fix:**
- Added regex validation for backup IDs (`^[a-f0-9-]+$`)
- Applied to all backup endpoints: restore, delete, verify
- Returns 400 Bad Request for invalid IDs

**File:** `app/routes/backups.py`

---

### 7. Debug Mode Enabled (MEDIUM)

**Issue:** Debug mode was enabled by default, which can leak stack traces and sensitive information.

**Fix:**
- Changed default `debug` setting from `True` to `False`
- Added startup security checks that warn if:
  - Debug mode is enabled in production
  - SECRET_KEY is not set or too short (< 32 chars)
  - ADMIN_PASSWORD is less than 12 characters

**Files:**
- `app/config.py`
- `app/main.py`

---

## Security Utilities Module

Created new `app/security_utils.py` module providing:

### `sanitize_filename(filename, allow_empty=False)`
Sanitizes filenames to prevent path traversal:
- Removes null bytes
- Strips path separators (`/` and `\`)
- Removes leading dots (hidden files)
- Replaces dangerous characters with underscores
- Limits length to 255 characters

### `validate_file_extension(filename, allowed_extensions)`
Validates file extensions against an allowlist.

### `is_safe_path(base_path, target_path)`
Verifies that a target path is within a base directory (prevents path traversal).

### `sanitize_email(email)`
Basic email sanitization and validation.

### `sanitize_string(input_str, max_length=1000, allow_html=False)`
General string sanitization for preventing injection attacks.

---

## Environment Variables Added

| Variable | Description | Required |
|----------|-------------|----------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins (e.g., `https://app.example.com,https://admin.example.com`) | Production |
| `ADMIN_PASSWORD` | Initial admin password (only used when no users exist) | On first run |
| `ADMIN_EMAIL` | Initial admin email (default: `admin@openmercura.local`) | No |

---

## Dependencies

### New Optional Dependency
- `bcrypt>=4.0.0` - Recommended for secure password hashing

If bcrypt is not installed, the system falls back to PBKDF2-SHA256 with 600,000 iterations.

---

## Verification Steps

To verify the security fixes are working:

1. **CORS:**
   ```bash
   curl -H "Origin: https://evil.com" -I http://localhost:8000/
   # Should not have Access-Control-Allow-Origin: https://evil.com in production
   ```

2. **File Upload Sanitization:**
   Try uploading a file with name `../../../etc/passwd.jpg` - should be sanitized to `etc_passwd.jpg`

3. **Backup Authorization:**
   Attempt to restore a backup as a non-admin user - should receive 403 Forbidden

4. **Password Hashing:**
   New passwords should be stored with bcrypt prefix `$2b$` (visible in database dumps)

---

## Additional Security Recommendations

1. **HTTPS Enforcement:**
   - Deploy with HTTPS in production
   - Set `Secure` and `HttpOnly` flags on cookies when implemented

2. **Rate Limiting:**
   - Already partially implemented via `RateLimitMiddleware`
   - Consider adding stricter limits on file uploads

3. **Content Security Policy (CSP):**
   - Add CSP headers to prevent XSS attacks

4. **Dependency Scanning:**
   - Regularly run `pip-audit` or `safety` to check for vulnerable dependencies

5. **Secrets Management:**
   - Use a proper secrets manager (AWS Secrets Manager, HashiCorp Vault) instead of environment variables for production

6. **SQL Injection Prevention:**
   - Current code uses parameterized queries correctly ✓
   - Continue to avoid string concatenation in SQL

7. **Session Management:**
   - Current in-memory token store should be replaced with Redis for production multi-instance deployments

---

## OWASP Top 10 Coverage

| Risk | Status | Notes |
|------|--------|-------|
| Broken Access Control | ✅ Mitigated | Added authorization checks, CORS restrictions |
| Cryptographic Failures | ✅ Mitigated | Upgraded password hashing to bcrypt |
| Injection | ✅ Mitigated | Parameterized queries, input sanitization |
| Insecure Design | ✅ Mitigated | Security-first filename handling |
| Security Misconfiguration | ✅ Mitigated | Debug mode disabled, security headers |
| Vulnerable Components | ⚠️ Monitor | Regular dependency audits recommended |
| Authentication Failures | ✅ Mitigated | Stronger password hashing, no default passwords |
| Software Integrity | ✅ Mitigated | Backup verification, checksum validation |
| Logging Failures | ✅ Mitigated | Comprehensive audit logging in place |
| SSRF | ✅ Mitigated | No external URL fetching from user input |

---

## Conclusion

All identified critical and high-severity security issues have been addressed. The application now follows security best practices for:
- Authentication (bcrypt password hashing)
- Authorization (role-based access control)
- Input validation (filename sanitization)
- Configuration security (CORS, debug mode)

Regular security audits should be conducted quarterly or after significant code changes.
