# CONTINUUM AI — SECURITY, PERMISSIONS & COMPLIANCE ARCHITECTURE
**Security Standard:** ISO/IEC 27001 Information Security Management  
**Version:** 2.0  
**Target:** Multi-Tenant Role Isolation & Cryptographic Audit Trails  

---

## 1. Security Overview & Threat Model

Technical handover platforms store an organization's most sensitive assets: architecture diagrams, proprietary source code references, database schemas, and identified vulnerabilities. Continuum AI implements **Defense in Depth** across authentication, access authorization, tenant isolation, and audit logging.

### Threat Model Mitigations:
1. **Cross-Tenant Project Access:** A member of Project A cannot view documents, employee passports, or source code commits of Project B.
2. **Unauthorized Handover Mutation:** Only authorized managers or administrators can initiate a handover or resolve contradictions.
3. **Successor Impersonation:** Only the designated successor or authorized administrators can sign and acknowledge a handover receipt.
4. **Credential Exposure:** Source code tokens and AI API keys are masked in preview representations (`ghp_****`).

---

## 2. Authentication & Session Security

- **Cryptographic Password Hashing:** Passwords are never stored in plaintext. They are salted and hashed using `bcrypt` (work factor 12) via `passlib.context.CryptContext`.
- **Stateless Bearer Tokens:** Authentication uses RFC 7519 JSON Web Tokens (JWT) signed with HS256 and verified on every protected request.
- **Token Invalidation & Expiration:** Tokens carry an explicit expiration time (`exp` claim, default 24 hours).
- **Client-Side Interceptor Guard:** The frontend Axios client automatically intercepts 401 Unauthorized responses, clears stored credentials, and redirects cleanly to `/login`.

---

## 3. Role-Based Access Control (RBAC) Matrix

Continuum AI defines four distinct organizational roles:

| Action / Capability | `ADMIN` | `PROJECT_MANAGER` | `TEAM_MEMBER` | `INCOMING_MEMBER` |
| :--- | :---: | :---: | :---: | :---: |
| **System Settings & AI Providers** | Yes | View Only | View Only | View Only |
| **Create / Delete Projects** | Yes | Yes (Owned) | No | No |
| **Upload / Delete Project Documents** | Yes | Yes | Yes | View Only |
| **Connect / Synchronize Git Repos** | Yes | Yes | Yes | View Only |
| **View Employee Knowledge Passports** | Yes | Yes | Yes | Yes |
| **Reconstruct Knowledge via AI** | Yes | Yes | Yes | View Only |
| **Initiate Employee Handover** | Yes | Yes | No | No |
| **Resolve Contradictions & Conflicts** | Yes | Yes | No | No |
| **Approve / Reject Handover Reports** | Yes | Yes | No | No |
| **Execute Continuation Checklist** | Yes | Yes | Yes | Yes |
| **Sign Handover Acknowledgment** | Yes | Yes | No | Yes (Successor) |
| **Query Ask Project AI Assistant** | Yes | Yes | Yes | Yes |
| **Export Evidence-Linked PDF Dossier**| Yes | Yes | Yes | Yes |

---

## 4. Multi-Tenant Project Isolation Implementation

Project isolation is enforced at the controller layer via the `check_project_access` FastAPI dependency:

```python
def check_project_access(project_id: int, current_user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Admins have global visibility
    if current_user.role == UserRole.ADMIN.value:
        return project

    # Check project ownership
    if project.owner_id == current_user.id:
        return project

    # Check project membership
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: You are not an authorized member of this project."
        )

    return project
```

---

## 5. Non-Repudiation & Audit Logging

Every critical platform action generates an immutable audit record in the `audit_logs` table:
- **Actor:** User ID and email of the initiator.
- **Action Type:** e.g. `HANDOVER_INITIATED`, `HANDOVER_ACKNOWLEDGED`, `CONFLICT_RESOLVED`, `REPORT_APPROVED`.
- **Entity Type & ID:** Affected project, report, or employee profile.
- **Details:** Full snapshot of changes, comments, and timestamps.
- **Tamper Resistance:** Audit log records cannot be edited or deleted through any client API endpoint.

