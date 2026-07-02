"""Tests for allocation service — concurrency-safe assignment creation."""

import threading
from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import (
    ConflictWithLeaveError,
    NotFoundError,
    OverAllocationError,
    ValidationError,
)
from app.models.models import Leave, LeaveStatus, LeaveType
from app.services.allocation_service import create_assignment, update_assignment


class TestCreateAssignment:
    def test_valid_creation(self, db: Session, team_member, instance):
        result = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=50,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        assert result.id is not None
        assert result.allocation_percent == 50
        assert result.team_member_id == team_member.id

    def test_over_allocation_blocked(self, db: Session, team_member, instance):
        # Create first assignment at 60%
        create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=60,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        # Try to create another at 50% — should exceed 100%
        with pytest.raises(OverAllocationError):
            create_assignment(
                db,
                team_member_id=team_member.id,
                engagement_instance_id=instance.id,
                allocation_percent=50,
                start_date=instance.start_date,
                end_date=instance.end_date,
            )

    def test_approved_leave_conflict(self, db: Session, team_member, instance):
        # Add approved leave that overlaps
        leave = Leave(
            team_member_id=team_member.id,
            leave_type=LeaveType.vacation,
            start_date=instance.start_date,
            end_date=instance.end_date,
            status=LeaveStatus.approved,
        )
        db.add(leave)
        db.commit()

        with pytest.raises(ConflictWithLeaveError):
            create_assignment(
                db,
                team_member_id=team_member.id,
                engagement_instance_id=instance.id,
                allocation_percent=50,
                start_date=instance.start_date,
                end_date=instance.end_date,
            )

    def test_pending_leave_does_not_conflict(self, db: Session, team_member, instance):
        leave = Leave(
            team_member_id=team_member.id,
            leave_type=LeaveType.sick,
            start_date=instance.start_date,
            end_date=instance.end_date,
            status=LeaveStatus.pending,
        )
        db.add(leave)
        db.commit()

        result = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=50,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        assert result.id is not None

    def test_inactive_member_raises(self, db: Session, team_member, instance):
        team_member.is_active = False
        db.commit()

        with pytest.raises(ValidationError):
            create_assignment(
                db,
                team_member_id=team_member.id,
                engagement_instance_id=instance.id,
                allocation_percent=50,
                start_date=instance.start_date,
                end_date=instance.end_date,
            )

    def test_nonexistent_member_raises(self, db: Session, instance):
        with pytest.raises(NotFoundError):
            create_assignment(
                db,
                team_member_id=99999,
                engagement_instance_id=instance.id,
                allocation_percent=50,
                start_date=instance.start_date,
                end_date=instance.end_date,
            )

    def test_invalid_allocation_percent(self, db: Session, team_member, instance):
        with pytest.raises(ValidationError):
            create_assignment(
                db,
                team_member_id=team_member.id,
                engagement_instance_id=instance.id,
                allocation_percent=0,
                start_date=instance.start_date,
                end_date=instance.end_date,
            )

    def test_end_date_before_start(self, db: Session, team_member, instance):
        with pytest.raises(ValidationError):
            create_assignment(
                db,
                team_member_id=team_member.id,
                engagement_instance_id=instance.id,
                allocation_percent=50,
                start_date=instance.end_date,
                end_date=instance.start_date,
            )


class TestUpdateAssignment:
    def test_update_allocation_revalidates(self, db: Session, team_member, instance):
        # Create first assignment at 60%
        a1 = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=60,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        # Create second assignment at 30% — should be OK (total 90%)
        a2 = create_assignment(
            db,
            team_member_id=team_member.id,
            engagement_instance_id=instance.id,
            allocation_percent=30,
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
        # Update a2 to 50% — would exceed 100%
        with pytest.raises(OverAllocationError):
            update_assignment(db, assignment_id=a2.id, allocation_percent=50)


class TestConcurrency:
    """Verify FOR UPDATE locking prevents double-booking under concurrent writes."""

    def test_concurrent_allocations_prevent_over_allocation(
        self, db: Session, team_member, instance
    ):
        """Two threads each try to allocate 70% simultaneously.

        Without row locking both would succeed (each sees 0% and adds 70%),
        resulting in 140% total. With FOR UPDATE, one must fail.
        """
        barrier = threading.Barrier(2, timeout=10)
        results = {}
        errors = {}

        def allocate(thread_name: str):
            session = SessionLocal()
            try:
                barrier.wait()  # both threads start at the same time
                create_assignment(
                    session,
                    team_member_id=team_member.id,
                    engagement_instance_id=instance.id,
                    allocation_percent=70,
                    start_date=instance.start_date,
                    end_date=instance.end_date,
                )
                results[thread_name] = "success"
            except OverAllocationError:
                errors[thread_name] = "over_allocation"
            except Exception as e:
                errors[thread_name] = f"unexpected: {type(e).__name__}: {e}"
            finally:
                session.close()

        t1 = threading.Thread(target=allocate, args=("t1",))
        t2 = threading.Thread(target=allocate, args=("t2",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one should succeed, one should fail with over-allocation
        assert len(results) == 1, f"Expected 1 success, got: {results}, errors: {errors}"
        assert len(errors) == 1, f"Expected 1 failure, got: {results}, errors: {errors}"
        assert "over_allocation" in errors.values()

        # Final state: only one 70% allocation exists
        final_db = SessionLocal()
        try:
            from app.models.models import Assignment

            count = (
                final_db.query(Assignment)
                .filter(Assignment.team_member_id == team_member.id)
                .count()
            )
            assert count == 1
            total = (
                final_db.query(
                    __import__("sqlalchemy").func.sum(Assignment.allocation_percent)
                )
                .filter(Assignment.team_member_id == team_member.id)
                .scalar()
            )
            assert total == 70
        finally:
            final_db.close()

    def test_concurrent_allocations_within_limit_both_succeed(
        self, db: Session, team_member, instance
    ):
        """Two threads each try to allocate 40% simultaneously.

        Total 80% is under 100%, so both should succeed.
        """
        barrier = threading.Barrier(2, timeout=10)
        results = {}

        def allocate(thread_name: str):
            session = SessionLocal()
            try:
                barrier.wait()
                create_assignment(
                    session,
                    team_member_id=team_member.id,
                    engagement_instance_id=instance.id,
                    allocation_percent=40,
                    start_date=instance.start_date,
                    end_date=instance.end_date,
                )
                results[thread_name] = "success"
            except Exception as e:
                results[thread_name] = f"error: {type(e).__name__}: {e}"
            finally:
                session.close()

        t1 = threading.Thread(target=allocate, args=("t1",))
        t2 = threading.Thread(target=allocate, args=("t2",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert all(v == "success" for v in results.values()), f"Results: {results}"

        # Final state: two 40% allocations = 80% total
        final_db = SessionLocal()
        try:
            from app.models.models import Assignment

            count = (
                final_db.query(Assignment)
                .filter(Assignment.team_member_id == team_member.id)
                .count()
            )
            assert count == 2
            total = (
                final_db.query(
                    __import__("sqlalchemy").func.sum(Assignment.allocation_percent)
                )
                .filter(Assignment.team_member_id == team_member.id)
                .scalar()
            )
            assert total == 80
        finally:
            final_db.close()
