"""Tests for email service — queue, process, retry, outbox admin."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.models import (
    Assignment,
    BusinessRole,
    Client,
    EmailOutbox,
    Engagement,
    EngagementInstance,
    EngagementStatus,
    EngagementType,
    InstanceStatus,
    RecurrencePattern,
    TeamMember,
    TechnicalRole,
    User,
)
from app.services.allocation_service import create_assignment
from app.services.email_service import (
    list_outbox,
    process_outbox,
    queue_assignment_notification,
    queue_email,
    retry_failed,
    send_outbox_entry,
)


def _auth_headers(user_id: int):
    return {"X-User-Id": str(user_id)}


class TestQueueEmail:
    def test_queue_email_creates_pending(self, db: Session):
        entry = queue_email(db, "test@example.com", "Subject", "Body")
        assert entry.id is not None
        assert entry.status == "pending"
        assert entry.recipient_email == "test@example.com"

    def test_queue_with_assignment_id(self, db: Session, team_member, instance):
        assignment = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=50,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        entry = queue_email(
            db, "test@example.com", "Subject", "Body", assignment_id=assignment.id
        )
        assert entry.assignment_id == assignment.id


class TestSendOutboxEntry:
    @patch("app.services.email_service._send_via_smtp")
    def test_successful_send(self, mock_smtp, db: Session):
        entry = queue_email(db, "test@example.com", "Subject", "Body")
        result = send_outbox_entry(db, entry.id)
        assert result is True
        db.refresh(entry)
        assert entry.status == "sent"
        assert entry.sent_at is not None
        assert entry.last_error is None
        mock_smtp.assert_called_once()

    @patch("app.services.email_service._send_via_smtp", side_effect=Exception("SMTP down"))
    def test_failed_send_increments_retry(self, mock_smtp, db: Session):
        entry = queue_email(db, "test@example.com", "Subject", "Body")
        result = send_outbox_entry(db, entry.id)
        assert result is False
        db.refresh(entry)
        assert entry.status == "pending"
        assert entry.retry_count == 1
        assert entry.last_error == "SMTP down"
        assert entry.next_attempt_at is not None

    @patch("app.services.email_service._send_via_smtp", side_effect=Exception("fail"))
    def test_max_retries_marks_failed(self, mock_smtp, db: Session):
        entry = queue_email(db, "test@example.com", "Subject", "Body")
        # Exhaust retries
        for _ in range(3):
            send_outbox_entry(db, entry.id)
        db.refresh(entry)
        assert entry.status == "failed"
        assert entry.retry_count == 3


class TestProcessOutbox:
    @patch("app.services.email_service._send_via_smtp")
    def test_processes_pending_batch(self, mock_smtp, db: Session):
        queue_email(db, "a@test.com", "A", "body a")
        queue_email(db, "b@test.com", "B", "body b")
        result = process_outbox(db)
        assert result["processed"] == 2
        assert result["sent"] == 2
        assert result["failed"] == 0

    @patch("app.services.email_service._send_via_smtp", side_effect=Exception("fail"))
    def test_handles_failures(self, mock_smtp, db: Session):
        queue_email(db, "a@test.com", "A", "body a")
        result = process_outbox(db)
        assert result["processed"] == 1
        assert result["sent"] == 0
        # First failure doesn't mark as failed (needs 3 retries)
        assert result["failed"] == 0

    def test_skips_future_retry_entries(self, db: Session):
        entry = queue_email(db, "a@test.com", "A", "body")
        from datetime import datetime, timezone

        entry.next_attempt_at = datetime.now(timezone.utc) + timedelta(hours=1)
        entry.retry_count = 1
        db.commit()
        result = process_outbox(db)
        assert result["processed"] == 0


class TestAssignmentNotification:
    def test_queues_email_on_assignment(self, db: Session, team_member, instance):
        assignment = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=50,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        # Check that an outbox entry was created
        entries = db.query(EmailOutbox).filter(EmailOutbox.assignment_id == assignment.id).all()
        assert len(entries) == 1
        assert entries[0].recipient_email == team_member.email
        assert "assignment" in entries[0].subject.lower() or "new" in entries[0].subject.lower()


class TestRetryFailed:
    def test_retry_resets_status(self, db: Session):
        entry = queue_email(db, "a@test.com", "A", "body")
        entry.status = "failed"
        entry.retry_count = 3
        entry.last_error = "permanent failure"
        db.commit()

        result = retry_failed(db, entry.id)
        assert result is True
        db.refresh(entry)
        assert entry.status == "pending"
        assert entry.retry_count == 0
        assert entry.last_error is None

    def test_retry_only_failed(self, db: Session):
        entry = queue_email(db, "a@test.com", "A", "body")
        result = retry_failed(db, entry.id)
        assert result is False


class TestOutboxAdmin:
    def test_admin_can_view_outbox(self, client, admin_user):
        response = client.get("/admin/outbox", headers=_auth_headers(admin_user.id))
        assert response.status_code == 200

    def test_viewer_denied_outbox(self, client, viewer_user):
        response = client.get("/admin/outbox", headers=_auth_headers(viewer_user.id))
        assert response.status_code == 403

    def test_admin_can_trigger_process(self, client, admin_user):
        response = client.post(
            "/admin/outbox/process",
            headers=_auth_headers(admin_user.id),
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_list_outbox_filters(self, db: Session):
        queue_email(db, "a@test.com", "Subject A", "body")
        entry = queue_email(db, "b@test.com", "Subject B", "body")
        entry.status = "sent"
        db.commit()

        items, total = list_outbox(db)
        assert total == 2

        items, total = list_outbox(db, status="pending")
        assert total == 1

        items, total = list_outbox(db, q="b@test")
        assert total == 1
