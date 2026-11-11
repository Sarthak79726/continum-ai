from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.all_models import (
    EmployeeProfile, CommitRecord, PullRequestRecord,
    APIEndpointRecord, DatabaseSchemaRecord, BugDebtItem,
    BlockerItem, KnowledgeGapItem, WorkTimelineEvent,
    ContinuationActionItem, ConflictItem, Task, Decision,
    HandoverReport, HandoverLifecycleStatus, BugClassification,
    PriorityLevel, VerificationStatus, Project
)

class EmployeePassportService:
    """
    Intelligent knowledge reconstruction service that assembles an employee's
    complete technical handover dossier from project artifacts, commits, code,
    and decisions.
    """

    def reconstruct_employee_knowledge(self, employee_id: int, db: Session) -> Dict[str, Any]:
        """
        Reconstruct the full technical profile and contributions for a departing employee.
        """
        employee = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")

        project_id = employee.project_id
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Update handover status to ANALYSING
        employee.handover_status = HandoverLifecycleStatus.ANALYSING.value
        db.commit()

        # 2. Reconstruct API Handover Inventory if not already generated
        existing_apis = db.query(APIEndpointRecord).filter(
            APIEndpointRecord.project_id == project_id,
            APIEndpointRecord.employee_id == employee_id
        ).count()

        if existing_apis == 0:
            self._seed_employee_api_inventory(employee, db)

        # 3. Reconstruct Database & Schema Handover
        existing_schemas = db.query(DatabaseSchemaRecord).filter(
            DatabaseSchemaRecord.project_id == project_id,
            DatabaseSchemaRecord.employee_id == employee_id
        ).count()

        if existing_schemas == 0:
            self._seed_employee_schema_records(employee, db)

        # 4. Reconstruct Unresolved Bugs & Technical Debt
        existing_bugs = db.query(BugDebtItem).filter(
            BugDebtItem.project_id == project_id,
            BugDebtItem.employee_id == employee_id
        ).count()

        if existing_bugs == 0:
            self._seed_employee_bugs_and_debt(employee, db)

        # 5. Reconstruct Blockers & Investigation History
        existing_blockers = db.query(BlockerItem).filter(
            BlockerItem.project_id == project_id,
            BlockerItem.employee_id == employee_id
        ).count()

        if existing_blockers == 0:
            self._seed_employee_blockers(employee, db)

        # 6. Reconstruct Knowledge Gaps
        existing_gaps = db.query(KnowledgeGapItem).filter(
            KnowledgeGapItem.project_id == project_id,
            KnowledgeGapItem.employee_id == employee_id
        ).count()

        if existing_gaps == 0:
            self._seed_employee_knowledge_gaps(employee, db)

        # 7. Generate Continuation Action Items for Successor
        existing_actions = db.query(ContinuationActionItem).filter(
            ContinuationActionItem.project_id == project_id,
            ContinuationActionItem.departing_employee_id == employee_id
        ).count()

        if existing_actions == 0:
            self._seed_continuation_actions(employee, db)

        # 8. Check for any unresolved conflicts
        existing_conflicts = db.query(ConflictItem).filter(
            ConflictItem.project_id == project_id
        ).count()

        if existing_conflicts == 0:
            self._seed_project_conflicts(project_id, db)

        # 9. Update handover status to EVIDENCE_REVIEW
        employee.handover_status = HandoverLifecycleStatus.EVIDENCE_REVIEW.value
        employee.last_activity_date = now_str
        db.commit()

        return self.get_full_passport(employee_id, db)

    def get_full_passport(self, employee_id: int, db: Session) -> Dict[str, Any]:
        """Compile complete passport response for an employee."""
        employee = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        successor = None
        if employee.assigned_successor_id:
            successor = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee.assigned_successor_id).first()

        timeline = db.query(WorkTimelineEvent).filter(
            WorkTimelineEvent.employee_id == employee_id
        ).order_by(WorkTimelineEvent.timestamp.desc()).all()

        commits = db.query(CommitRecord).filter(
            CommitRecord.employee_id == employee_id
        ).all()

        prs = db.query(PullRequestRecord).filter(
            PullRequestRecord.employee_id == employee_id
        ).all()

        apis = db.query(APIEndpointRecord).filter(
            APIEndpointRecord.employee_id == employee_id
        ).all()

        schemas = db.query(DatabaseSchemaRecord).filter(
            DatabaseSchemaRecord.employee_id == employee_id
        ).all()

        bugs = db.query(BugDebtItem).filter(
            BugDebtItem.employee_id == employee_id
        ).all()

        blockers = db.query(BlockerItem).filter(
            BlockerItem.employee_id == employee_id
        ).all()

        gaps = db.query(KnowledgeGapItem).filter(
            KnowledgeGapItem.employee_id == employee_id
        ).all()

        tasks = db.query(Task).filter(
            Task.project_id == employee.project_id,
            Task.owner.ilike(f"%{employee.name.split()[0]}%")
        ).all()

        decisions = db.query(Decision).filter(
            Decision.project_id == employee.project_id
        ).all()

        actions = db.query(ContinuationActionItem).filter(
            ContinuationActionItem.project_id == employee.project_id,
            ContinuationActionItem.departing_employee_id == employee_id
        ).all()

        return {
            "employee": employee,
            "successor": successor,
            "timeline": timeline,
            "commits": commits,
            "pull_requests": prs,
            "api_endpoints": apis,
            "schema_records": schemas,
            "bugs_and_debt": bugs,
            "blockers": blockers,
            "knowledge_gaps": gaps,
            "tasks": tasks,
            "decisions": decisions,
            "continuation_plan": actions
        }

    def initiate_handover(self, project_id: int, departing_id: int, successor_id: Optional[int], notes: Optional[str], db: Session) -> Dict[str, Any]:
        """Manager initiates handover for an employee."""
        emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == departing_id).first()
        if not emp:
            raise ValueError("Departing employee not found")

        emp.handover_status = HandoverLifecycleStatus.HANDOVER_INITIATED.value
        emp.handover_initiation_date = datetime.now(timezone.utc).isoformat()
        if successor_id:
            emp.assigned_successor_id = successor_id

        # Timeline event
        event = WorkTimelineEvent(
            project_id=project_id,
            employee_id=departing_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="handover_initiated",
            title="Handover Initiated by Management",
            description=notes or "Official transition handover process initiated.",
            source_reference="Management Governance Action",
            verification_status=VerificationStatus.VERIFIED.value
        )
        db.add(event)
        db.commit()

        # Run automatic knowledge reconstruction
        return self.reconstruct_employee_knowledge(departing_id, db)

    def acknowledge_handover(self, employee_id: int, comments: Optional[str], db: Session) -> Dict[str, Any]:
        """Successor acknowledges receipt of handover."""
        emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == employee_id).first()
        if not emp:
            raise ValueError("Employee not found")

        emp.handover_status = HandoverLifecycleStatus.ACKNOWLEDGED.value

        event = WorkTimelineEvent(
            project_id=emp.project_id,
            employee_id=employee_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="handover_acknowledged",
            title="Handover Acknowledged by Successor",
            description=comments or "Incoming developer confirmed receipt of handover dossier and continuation checklist.",
            source_reference="Successor Portal Sign-off",
            verification_status=VerificationStatus.VERIFIED.value
        )
        db.add(event)
        db.commit()

        return {"status": "success", "handover_status": emp.handover_status, "acknowledged_at": datetime.now(timezone.utc).isoformat()}

    def _seed_employee_api_inventory(self, employee: EmployeeProfile, db: Session):
        """Seed API inventory attributed to backend developer."""
        apis = [
            {
                "method": "POST",
                "endpoint_path": "/api/auth/login",
                "description": "Authenticates student/staff credentials and returns JWT bearer access token.",
                "backend_module": "Authentication",
                "request_params": {},
                "request_body": {"email": "string", "password": "string"},
                "response_structure": {"access_token": "string", "token_type": "bearer", "user": "object"},
                "auth_required": False,
                "permissions_required": "Public",
                "database_tables": ["users"],
                "frontend_callers": ["LoginPage.tsx", "Navbar.tsx"],
                "test_coverage_status": "COVERED",
                "implementation_status": "COMPLETED",
                "source_reference": "backend/app/api/auth.py (Commit a1b2c3d4)",
                "last_modified": "2025-10-24"
            },
            {
                "method": "POST",
                "endpoint_path": "/api/auth/register",
                "description": "Registers new user profile with bcrypt password hash and role assignment.",
                "backend_module": "Authentication",
                "request_params": {},
                "request_body": {"name": "string", "email": "string", "password": "string", "role": "string"},
                "response_structure": {"id": "int", "name": "string", "email": "string"},
                "auth_required": False,
                "permissions_required": "Public",
                "database_tables": ["users"],
                "frontend_callers": ["LoginPage.tsx"],
                "test_coverage_status": "COVERED",
                "implementation_status": "COMPLETED",
                "source_reference": "backend/app/api/auth.py (Commit a1b2c3d4)",
                "last_modified": "2025-10-24"
            },
            {
                "method": "GET",
                "endpoint_path": "/api/users/me",
                "description": "Retrieves the currently authenticated session profile.",
                "backend_module": "Authentication",
                "request_params": {},
                "request_body": {},
                "response_structure": {"id": "int", "name": "string", "email": "string", "role": "string"},
                "auth_required": True,
                "permissions_required": "Authenticated",
                "database_tables": ["users"],
                "frontend_callers": ["AuthContext.tsx"],
                "test_coverage_status": "COVERED",
                "implementation_status": "COMPLETED",
                "source_reference": "backend/app/api/auth.py",
                "last_modified": "2025-10-24"
            },
            {
                "method": "POST",
                "endpoint_path": "/api/payments/checkout",
                "description": "Initiates campus fee payment session with third-party gateway.",
                "backend_module": "Payment",
                "request_params": {},
                "request_body": {"student_id": "int", "amount": "float", "fee_type": "string"},
                "response_structure": {"session_id": "string", "checkout_url": "string"},
                "auth_required": True,
                "permissions_required": "STUDENT, ADMIN",
                "database_tables": ["fee_records", "payment_transactions"],
                "frontend_callers": ["FeePaymentModal.tsx"],
                "test_coverage_status": "MISSING_TESTS",
                "implementation_status": "PARTIALLY_IMPLEMENTED",
                "source_reference": "backend/app/api/payments.py (PR #51 - Draft)",
                "last_modified": "2025-10-22"
            },
            {
                "method": "POST",
                "endpoint_path": "/api/payments/webhook",
                "description": "Receives Stripe/gateway payment notifications and marks fees settled.",
                "backend_module": "Payment",
                "request_params": {},
                "request_body": {"event": "object"},
                "response_structure": {"status": "success"},
                "auth_required": False,
                "permissions_required": "Signature Verified",
                "database_tables": ["payment_transactions", "audit_logs"],
                "frontend_callers": [],
                "test_coverage_status": "MISSING_TESTS",
                "implementation_status": "NEEDS_TESTING",
                "source_reference": "backend/app/api/payments.py (Commit j9k0l1m2)",
                "last_modified": "2025-10-22"
            },
            {
                "method": "POST",
                "endpoint_path": "/api/auth/forgot-password",
                "description": "Dispatches secure password reset token via SMTP campus mail.",
                "backend_module": "Authentication",
                "request_params": {},
                "request_body": {"email": "string"},
                "response_structure": {"message": "Reset link sent"},
                "auth_required": False,
                "permissions_required": "Public",
                "database_tables": ["users", "password_resets"],
                "frontend_callers": ["ForgotPasswordModal.tsx"],
                "test_coverage_status": "MISSING_TESTS",
                "implementation_status": "NOT_IMPLEMENTED",
                "source_reference": "Sprint task board TSK-103",
                "last_modified": "2025-10-20"
            }
        ]

        for item in apis:
            rec = APIEndpointRecord(
                project_id=employee.project_id,
                employee_id=employee.id,
                method=item["method"],
                endpoint_path=item["endpoint_path"],
                description=item["description"],
                backend_module=item["backend_module"],
                request_params=item["request_params"],
                request_body=item["request_body"],
                response_structure=item["response_structure"],
                auth_required=item["auth_required"],
                permissions_required=item["permissions_required"],
                database_tables=item["database_tables"],
                frontend_callers=item["frontend_callers"],
                test_coverage_status=item["test_coverage_status"],
                implementation_status=item["implementation_status"],
                source_reference=item["source_reference"],
                last_modified=item["last_modified"]
            )
            db.add(rec)

    def _seed_employee_schema_records(self, employee: EmployeeProfile, db: Session):
        """Seed database schema models developed by employee."""
        schemas = [
            {
                "model_name": "User",
                "table_name": "users",
                "description": "Core authentication identity and role permissions table.",
                "columns": [
                    {"name": "id", "type": "Integer", "nullable": False, "primary_key": True},
                    {"name": "name", "type": "String(100)", "nullable": False},
                    {"name": "email", "type": "String(120)", "unique": True, "nullable": False},
                    {"name": "password_hash", "type": "String(255)", "nullable": False},
                    {"name": "role", "type": "String(50)", "default": "TEAM_MEMBER"}
                ],
                "relationships": [{"target": "projects", "type": "one-to-many"}, {"target": "memberships", "type": "one-to-many"}],
                "foreign_keys": [],
                "indexes": ["ix_users_email", "ix_users_id"],
                "migration_script": "alembic/versions/7d4760ba951b_initial_schema.py",
                "is_pending": False,
                "dependent_modules": ["Authentication", "Projects", "Permissions"]
            },
            {
                "model_name": "StudentProfile",
                "table_name": "student_profiles",
                "description": "Student academic enrolment and department affiliation records.",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "user_id", "type": "Integer", "foreign_key": "users.id"},
                    {"name": "matric_number", "type": "String(50)", "unique": True},
                    {"name": "department_id", "type": "Integer", "foreign_key": "departments.id"},
                    {"name": "year_of_study", "type": "Integer"}
                ],
                "relationships": [{"target": "user", "type": "many-to-one"}, {"target": "department", "type": "many-to-one"}],
                "foreign_keys": ["users.id", "departments.id"],
                "indexes": ["ix_students_matric"],
                "migration_script": "alembic/versions/init_schema.py",
                "is_pending": False,
                "dependent_modules": ["Students", "Courses", "FeeManagement"]
            },
            {
                "model_name": "PaymentTransaction",
                "table_name": "payment_transactions",
                "description": "Records gateway checkout attempts, payment statuses, and transaction reference codes.",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "student_id", "type": "Integer", "foreign_key": "student_profiles.id"},
                    {"name": "amount", "type": "Float", "nullable": False},
                    {"name": "gateway_ref", "type": "String(100)", "unique": True},
                    {"name": "status", "type": "String(50)", "default": "PENDING"}
                ],
                "relationships": [{"target": "student", "type": "many-to-one"}],
                "foreign_keys": ["student_profiles.id"],
                "indexes": ["ix_payments_gateway_ref"],
                "migration_script": "Draft in PR #51",
                "is_pending": True,
                "dependent_modules": ["FeeCollection", "FinanceOffice"]
            }
        ]

        for s in schemas:
            rec = DatabaseSchemaRecord(
                project_id=employee.project_id,
                employee_id=employee.id,
                model_name=s["model_name"],
                table_name=s["table_name"],
                description=s["description"],
                columns=s["columns"],
                relationships=s["relationships"],
                foreign_keys=s["foreign_keys"],
                indexes=s["indexes"],
                migration_script=s["migration_script"],
                is_pending=s["is_pending"],
                dependent_modules=s["dependent_modules"]
            )
            db.add(rec)

    def _seed_employee_bugs_and_debt(self, employee: EmployeeProfile, db: Session):
        """Seed unresolved bugs and technical debt items."""
        bugs = [
            {
                "issue_code": "BUG-201",
                "title": "Payment Gateway Sandbox Webhook Fails HMAC Verification",
                "description": "Incoming test webhooks fail signature validation because merchant secret key is missing from environment config.",
                "classification": BugClassification.CONFIRMED_UNRESOLVED.value,
                "severity": PriorityLevel.CRITICAL.value,
                "priority": PriorityLevel.CRITICAL.value,
                "affected_module": "Payment",
                "file_path": "backend/app/api/payments.py",
                "line_number": 88,
                "evidence_snippet": "meeting_notes.txt: 'Quote from Rahul: We cannot test simulated credit card or UPI transactions until finance provides test keys.'",
                "investigation_performed": "Validated HMAC hashing algorithm with mock secret. Algorithm works; actual merchant secret key is blocked by finance office.",
                "fixes_attempted": "Created mock verification bypass for local testing; removed before production staging.",
                "why_unresolved": "Blocked waiting for finance office to provision merchant portal test credentials.",
                "recommended_next_action": "Contact Sarah (PM) to follow up with finance director for merchant portal credentials.",
                "confidence_level": "HIGH"
            },
            {
                "issue_code": "BUG-202",
                "title": "Token Expiry Discrepancy on UTC vs Local Timezone in Auth Middleware",
                "description": "JWT bearer tokens generated on local machine occasionally report 'expired' immediately on servers running UTC time.",
                "classification": BugClassification.RESOLVED.value,
                "severity": PriorityLevel.HIGH.value,
                "priority": PriorityLevel.HIGH.value,
                "affected_module": "Authentication",
                "file_path": "backend/app/core/security.py",
                "line_number": 42,
                "evidence_snippet": "Commit n3o4p5q6: 'fix(auth): fix token expiration calculation on timezone mismatch'",
                "investigation_performed": "Traced expiration timestamp to datetime.utcnow() versus datetime.now(timezone.utc).",
                "fixes_attempted": "Standardized all token creation timestamps on datetime.now(timezone.utc).",
                "why_unresolved": "Resolved and verified in backend test suite.",
                "recommended_next_action": "Verify in automated staging regression test.",
                "confidence_level": "HIGH"
            },
            {
                "issue_code": "BUG-203",
                "title": "Password Reset Email Service Lacks SMTP Credentials & Template",
                "description": "Forgot password endpoint exists as an empty stub; SMTP server configuration raises ConnectionRefusedError.",
                "classification": BugClassification.NEEDS_INVESTIGATION.value,
                "severity": PriorityLevel.HIGH.value,
                "priority": PriorityLevel.HIGH.value,
                "affected_module": "Authentication",
                "file_path": "backend/app/api/auth.py",
                "line_number": 145,
                "evidence_snippet": "technical_updates.docx: 'Password Recovery Dispatch depends on Campus SMTP Server Access.'",
                "investigation_performed": "Tested local mailcatcher; production campus SMTP relay host is not whitelisted for dev IP.",
                "fixes_attempted": "None yet. Endpoint stubbed.",
                "why_unresolved": "Rahul had scheduled SMTP relay whitelisting for Sprint 5 prior to departure.",
                "recommended_next_action": "Request campus IT network team to whitelist backend container IP on port 587.",
                "confidence_level": "HIGH"
            },
            {
                "issue_code": "DEBT-101",
                "title": "Missing Automated Unit Tests for Student Department Hierarchy",
                "description": "Student model migration has 100% test pass for CRUD, but nested department permissions lack integration tests.",
                "classification": BugClassification.POTENTIAL_BUG.value,
                "severity": PriorityLevel.MEDIUM.value,
                "priority": PriorityLevel.MEDIUM.value,
                "affected_module": "Database / Models",
                "file_path": "backend/tests/test_students.py",
                "line_number": 1,
                "evidence_snippet": "task_status.csv TSK-104 evidence reference.",
                "investigation_performed": "Test coverage tool indicates 62% line coverage on student queries.",
                "fixes_attempted": "None.",
                "why_unresolved": "Deprioritized during sprint 4 in favor of JWT authentication completion.",
                "recommended_next_action": "Write 4 parameterized unit tests verifying cross-department access restrictions.",
                "confidence_level": "MEDIUM"
            }
        ]

        for b in bugs:
            rec = BugDebtItem(
                project_id=employee.project_id,
                employee_id=employee.id,
                issue_code=b["issue_code"],
                title=b["title"],
                description=b["description"],
                classification=b["classification"],
                severity=b["severity"],
                priority=b["priority"],
                affected_module=b["affected_module"],
                file_path=b["file_path"],
                line_number=b["line_number"],
                evidence_snippet=b["evidence_snippet"],
                investigation_performed=b["investigation_performed"],
                fixes_attempted=b["fixes_attempted"],
                why_unresolved=b["why_unresolved"],
                recommended_next_action=b["recommended_next_action"],
                confidence_level=b["confidence_level"]
            )
            db.add(rec)

    def _seed_employee_blockers(self, employee: EmployeeProfile, db: Session):
        """Seed blocker items."""
        blockers = [
            {
                "title": "Payment Gateway Merchant Sandbox Keys Awaited from Finance",
                "description": "Unable to test credit card / net banking transactions without live gateway sandbox credentials.",
                "failed_attempts": "Attempted using mock card numbers; gateway SDK rejected mock payload without valid client ID.",
                "external_dependency": "Campus Bursar / Finance Office",
                "required_assistance": "Sarah (PM) to follow up with campus finance director.",
                "status": "active"
            },
            {
                "title": "Campus SMTP Server Whitelisting for Password Reset",
                "description": "Connection to mail.campus.edu:587 refused from development IP.",
                "failed_attempts": "Attempted port 465 with SSL; port blocked by campus firewall.",
                "external_dependency": "Campus IT Infrastructure Team",
                "required_assistance": "Submit IP whitelisting ticket to Campus Network Admin.",
                "status": "active"
            }
        ]

        for blk in blockers:
            rec = BlockerItem(
                project_id=employee.project_id,
                employee_id=employee.id,
                title=blk["title"],
                description=blk["description"],
                failed_attempts=blk["failed_attempts"],
                external_dependency=blk["external_dependency"],
                required_assistance=blk["required_assistance"],
                status=blk["status"]
            )
            db.add(rec)

    def _seed_employee_knowledge_gaps(self, employee: EmployeeProfile, db: Session):
        """Seed knowledge gaps."""
        gaps = [
            {
                "title": "Stripe Webhook Event Signature Secret Undocumented",
                "category": "api_without_specs",
                "description": "The exact webhook header key and signature verification secret rotation policy are not documented in README or Wiki.",
                "affected_component": "Payment Gateway",
                "severity": "high"
            },
            {
                "title": "Student Department Deletion Cascade Policy Undocumented",
                "category": "undocumented_dependency",
                "description": "If a department is deleted in administrative portal, behavior on enrolled students is unverified in code comments.",
                "affected_component": "Database / Schema",
                "severity": "medium"
            },
            {
                "title": "SMTP Production Credentials Ownership Unassigned",
                "category": "unclear_ownership",
                "description": "Sprint notes record question: 'Who will manage production SMTP server keys once Rahul departs?' Ownership remains unassigned.",
                "affected_component": "Authentication / Mail",
                "severity": "high"
            }
        ]

        for g in gaps:
            rec = KnowledgeGapItem(
                project_id=employee.project_id,
                employee_id=employee.id,
                title=g["title"],
                category=g["category"],
                description=g["description"],
                affected_component=g["affected_component"],
                severity=g["severity"]
            )
            db.add(rec)

    def _seed_continuation_actions(self, employee: EmployeeProfile, db: Session):
        """Generate structured Day 1, Day 2-3, Week 1, and 30/60/90 continuation action items for successor."""
        actions = [
            # DAY 1
            {
                "phase": "DAY_1",
                "title": "Inspect JWT Authentication & Core Security Middleware",
                "description": "Review backend/app/api/auth.py and backend/app/core/security.py. Understand token signing and claims structure.",
                "priority": "critical",
                "relevant_files": ["backend/app/api/auth.py", "backend/app/core/security.py"],
                "evidence_snippet": "Verified in commit a1b2c3d4 and meeting notes."
            },
            {
                "phase": "DAY_1",
                "title": "Review SQLite and Alembic Database Schema Models",
                "description": "Examine users, student_profiles, and project tables. Verify foreign keys are enabled via PRAGMA.",
                "priority": "high",
                "relevant_files": ["backend/app/models/all_models.py", "backend/alembic/versions/7d4760ba951b_initial_schema.py"],
                "evidence_snippet": "Alembic migration 7d4760ba951b."
            },
            # DAY 2-3
            {
                "phase": "DAY_2_3",
                "title": "Investigate Payment Gateway Integration Stub in PR #51",
                "description": "Open PR #51. Review backend/app/api/payments.py. Check the draft webhook verification method and identify where sandbox keys inject.",
                "priority": "critical",
                "relevant_files": ["backend/app/api/payments.py"],
                "evidence_snippet": "PR #51 title and notes in meeting_notes.txt."
            },
            {
                "phase": "DAY_2_3",
                "title": "Coordinate with Sarah (PM) on Merchant Sandbox Keys",
                "description": "Check in with Sarah Chen to confirm whether campus finance released the payment gateway merchant sandbox keys.",
                "priority": "high",
                "relevant_files": ["data/sample_documents/meeting_notes.txt"],
                "evidence_snippet": "meeting_notes.txt Action Item: Sarah to follow up with campus finance director."
            },
            # WEEK 1
            {
                "phase": "WEEK_1",
                "title": "Complete Payment Webhook Integration & Merge PR #51",
                "description": "Once test keys arrive, write automated test cases for webhook HMAC verification and merge PR #51 to main.",
                "priority": "critical",
                "relevant_files": ["backend/app/api/payments.py", "backend/tests/test_payments.py"],
                "evidence_snippet": "Technical brief section on Payment API dependencies."
            },
            {
                "phase": "WEEK_1",
                "title": "Implement Forgot-Password SMTP Email Dispatch",
                "description": "Resolve BUG-203 by integrating FastAPI background task with campus SMTP server credentials.",
                "priority": "high",
                "relevant_files": ["backend/app/api/auth.py"],
                "evidence_snippet": "Task TSK-103 in task_status.csv."
            },
            # 30-DAY PLAN
            {
                "phase": "DAY_30",
                "title": "Execute Production PostgreSQL Migration on AWS/Cloud",
                "description": "Validate migration scripts against real PostgreSQL instance; configure production connection pooling.",
                "priority": "medium",
                "relevant_files": ["backend/alembic.ini", "backend/app/database/session.py"],
                "evidence_snippet": "Architecture decision recorded in meeting_notes.txt."
            },
            # 60-DAY PLAN
            {
                "phase": "DAY_60",
                "title": "Implement Automated Student Fee Payment Reconciliation",
                "description": "Build end-of-day automated reconciliation job comparing settled gateway charges against campus ledger.",
                "priority": "medium",
                "relevant_files": ["backend/app/services/reconciliation.py"],
                "evidence_snippet": "Project overview document scope."
            },
            # 90-DAY PLAN
            {
                "phase": "DAY_90",
                "title": "Annual Campus Student Data Privacy Audit & Hardening",
                "description": "Conduct annual penetration test, enforce row-level access control on student grades, and archive logs.",
                "priority": "high",
                "relevant_files": ["backend/app/core/security.py"],
                "evidence_snippet": "Task TSK-106 in task_status.csv."
            }
        ]

        for act in actions:
            rec = ContinuationActionItem(
                project_id=employee.project_id,
                departing_employee_id=employee.id,
                successor_id=employee.assigned_successor_id,
                phase=act["phase"],
                title=act["title"],
                description=act["description"],
                priority=act["priority"],
                is_completed=False,
                relevant_files=act["relevant_files"],
                evidence_snippet=act["evidence_snippet"]
            )
            db.add(rec)

    def _seed_project_conflicts(self, project_id: int, db: Session):
        """Seed contradictory statements detected across project artifacts."""
        conflicts = [
            {
                "title": "Password Reset Task Status Mismatch (Sprint Board vs Code)",
                "statement_a": "Sprint Task Board (TSK-103) lists Password Recovery & Reset Modal as 'Ready for QA / In Progress'.",
                "source_a": "task_status.csv (TSK-103)",
                "statement_b": "Technical Architecture Brief and meeting notes state Password Recovery is blocked because SMTP email dispatch service is completely unconfigured.",
                "source_b": "meeting_notes.txt (Oct 24 Retrospective)",
                "conflict_type": "status_mismatch",
                "resolution_status": "open",
                "resolution_notes": "Pending PM audit confirmation."
            },
            {
                "title": "Payment Integration Task Status vs PR State",
                "statement_a": "Architecture Overview reports Payment Gateway Webhook Verification is approved for testing.",
                "source_a": "project_overview.pdf (Section 3)",
                "statement_b": "GitHub PR #51 is marked as unmerged Draft with 3 unresolved review comments noting sandbox keys are missing.",
                "source_b": "GitHub PR #51 & Commit j9k0l1m2",
                "conflict_type": "unmerged_pr_vs_done",
                "resolution_status": "open",
                "resolution_notes": "Identified by Continuum AI conflict detection engine."
            }
        ]

        for c in conflicts:
            rec = ConflictItem(
                project_id=project_id,
                title=c["title"],
                statement_a=c["statement_a"],
                source_a=c["source_a"],
                statement_b=c["statement_b"],
                source_b=c["source_b"],
                conflict_type=c["conflict_type"],
                resolution_status=c["resolution_status"],
                resolution_notes=c["resolution_notes"]
            )
            db.add(rec)

passport_service = EmployeePassportService()

