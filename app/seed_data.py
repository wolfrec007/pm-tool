"""Seed realistic demo data for the splanly dashboard.
Run:  py -m app.seed_data
"""
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.models.models import (
    Base, TeamMember, Client, Engagement, EngagementInstance,
    Assignment, Leave, BusinessRole, EngagementStatus,
    InstanceStatus, EngagementType, RecurrencePattern, LeaveStatus, LeaveType,
)

TODAY = date.today()

TEAM = [
    ("Rajesh Kumar",     "rajesh@pkf.in",     BusinessRole.partner),
    ("Priya Sharma",     "priya@pkf.in",      BusinessRole.director),
    ("Amit Deshmukh",    "amit@pkf.in",       BusinessRole.ca_manager),
    ("Sneha Iyer",       "sneha@pkf.in",      BusinessRole.ca_manager),
    ("Rohan Patel",      "rohan@pkf.in",      BusinessRole.staff),
    ("Neha Gupta",       "neha@pkf.in",       BusinessRole.staff),
    ("Vikram Singh",     "vikram@pkf.in",     BusinessRole.staff),
    ("Anjali Mehta",     "anjali@pkf.in",     BusinessRole.staff),
    ("Karan Joshi",      "karan@pkf.in",      BusinessRole.staff),
    ("Pooja Nair",       "pooja@pkf.in",      BusinessRole.paid_assistant),
    ("Deepak Reddy",     "deepak@pkf.in",     BusinessRole.paid_assistant),
    ("Meera Chopra",     "meera@pkf.in",      BusinessRole.article),
    ("Arjun Bose",       "arjun@pkf.in",      BusinessRole.article),
    ("Divya Menon",      "divya@pkf.in",      BusinessRole.article),
    ("Suresh Kumar",     "suresh@pkf.in",     BusinessRole.staff),
    ("Kavitha Rajan",    "kavitha@pkf.in",    BusinessRole.data_analyst),
]

CLIENTS = [
    ("Tata Consultancy Services", "tcs"),
    ("Infosys Limited", "infosys"),
    ("Wipro Enterprises", "wipro"),
    ("Reliance Industries", "reliance"),
    ("HDFC Bank", "hdfc"),
    ("Bajaj Auto", "bajaj"),
]

ENGAGEMENTS = [
    ("FY 2025-26 Statutory Audit",       "tcs",    EngagementType.statutory_audit,  RecurrencePattern.annual),
    ("Q1 2026 Tax Compliance",           "infosys", EngagementType.tax_audit,        RecurrencePattern.quarterly),
    ("GST Annual Return Filing",         "wipro",  EngagementType.consulting,       RecurrencePattern.annual),
    ("Transfer Pricing Documentation",   "reliance", EngagementType.consulting,      RecurrencePattern.annual),
    ("Internal Audit - IT Controls",     "hdfc",   EngagementType.internal_audit,   RecurrencePattern.quarterly),
    ("Statutory Audit FY 2025-26",       "bajaj",  EngagementType.statutory_audit,  RecurrencePattern.annual),
    ("Due Diligence - Acquisition",      "tcs",    EngagementType.special_assignment, RecurrencePattern.one_off),
    ("GST Monthly Compliance",           "reliance", EngagementType.consulting,      RecurrencePattern.monthly),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Get the first firm
        from app.models.models import Firm
        firm = db.query(Firm).first()
        if not firm:
            print("No firm found. Please create a firm first.")
            return
        firm_id = firm.id

        # ── Clients ──
        client_map = {}
        for name, code in CLIENTS:
            c = Client(name=name, code=code.upper(), firm_id=firm_id, is_active=True)
            db.add(c)
            db.flush()
            client_map[code] = c

        # ── Team Members ──
        members = []
        for name, email, role in TEAM:
            m = TeamMember(
                name=name, email=email, business_role=role, firm_id=firm_id,
                is_active=True, is_oversight_only=(role in (BusinessRole.partner, BusinessRole.director)),
            )
            db.add(m)
            db.flush()
            members.append(m)

        # ── Engagements + Instances ──
        eng_map = {}
        for eng_name, client_code, etype, recurrence in ENGAGEMENTS:
            e = Engagement(
                name=eng_name, client_id=client_map[client_code].id,
                engagement_type=etype, recurrence_pattern=recurrence,
                status=EngagementStatus.active,
                start_date=TODAY - timedelta(days=random.randint(30, 180)),
                end_date=TODAY + timedelta(days=random.randint(60, 300)),
            )
            db.add(e)
            db.flush()
            eng_map[eng_name] = e

            inst = EngagementInstance(
                engagement_id=e.id,
                period_label=f"{eng_name} — Phase 1",
                start_date=e.start_date,
                end_date=e.end_date,
                status=InstanceStatus.in_progress,
            )
            db.add(inst)
            db.flush()
            eng_map[eng_name + "_inst"] = inst

        # ── Assignments ──
        # Give partners/directors light oversight, managers full, staff varied
        assignments_data = [
            # Rajesh Kumar (partner) — light oversight
            ("Rajesh Kumar",  "FY 2025-26 Statutory Audit", 20, -90, 180),
            ("Rajesh Kumar",  "Transfer Pricing Documentation", 15, -60, 200),
            # Priya Sharma (director)
            ("Priya Sharma",  "Q1 2026 Tax Compliance", 30, -45, 120),
            ("Priya Sharma",  "GST Annual Return Filing", 25, -30, 90),
            ("Priya Sharma",  "Internal Audit - IT Controls", 20, -20, 150),
            # Amit Deshmukh (ca_manager) — heavily loaded
            ("Amit Deshmukh", "FY 2025-26 Statutory Audit", 40, -90, 180),
            ("Amit Deshmukh", "GST Annual Return Filing", 35, -30, 90),
            ("Amit Deshmukh", "Internal Audit - IT Controls", 30, -20, 150),
            # Sneha Iyer (ca_manager)
            ("Sneha Iyer",    "Q1 2026 Tax Compliance", 40, -45, 120),
            ("Sneha Iyer",    "Statutory Audit FY 2025-26", 35, -60, 200),
            # Rohan Patel (staff)
            ("Rohan Patel",   "FY 2025-26 Statutory Audit", 50, -90, 180),
            ("Rohan Patel",   "GST Annual Return Filing", 30, -30, 90),
            # Neha Gupta (staff)
            ("Neha Gupta",    "Q1 2026 Tax Compliance", 60, -45, 120),
            ("Neha Gupta",    "Transfer Pricing Documentation", 25, -60, 200),
            # Vikram Singh (staff)
            ("Vikram Singh",  "FY 2025-26 Statutory Audit", 45, -90, 180),
            ("Vikram Singh",  "Statutory Audit FY 2025-26", 40, -60, 200),
            # Anjali Mehta (staff)
            ("Anjali Mehta",  "GST Monthly Compliance", 50, -15, 60),
            ("Anjali Mehta",  "GST Annual Return Filing", 30, -30, 90),
            # Karan Joshi (staff)
            ("Karan Joshi",   "Internal Audit - IT Controls", 55, -20, 150),
            ("Karan Joshi",   "Due Diligence - Acquisition", 35, -10, 90),
            # Pooja Nair (paid_assistant)
            ("Pooja Nair",    "GST Monthly Compliance", 40, -15, 60),
            ("Pooja Nair",    "GST Annual Return Filing", 35, -30, 90),
            # Deepak Reddy (paid_assistant)
            ("Deepak Reddy",  "Transfer Pricing Documentation", 45, -60, 200),
            ("Deepak Reddy",  "Q1 2026 Tax Compliance", 30, -45, 120),
            # Meera Chopra (article)
            ("Meera Chopra",  "FY 2025-26 Statutory Audit", 50, -90, 180),
            # Arjun Bose (article)
            ("Arjun Bose",    "Statutory Audit FY 2025-26", 45, -60, 200),
            # Divya Menon (article) — bench
            # Suresh Kumar (staff)
            ("Suresh Kumar",  "Internal Audit - IT Controls", 60, -20, 150),
            ("Suresh Kumar",  "GST Monthly Compliance", 25, -15, 60),
        ]

        for member_name, eng_name, alloc, start_offset, duration in assignments_data:
            member = next(m for m in members if m.name == member_name)
            inst = eng_map.get(eng_name + "_inst")
            if not inst:
                continue
            a = Assignment(
                team_member_id=member.id,
                engagement_instance_id=inst.id,
                allocation_percent=alloc,
                start_date=TODAY + timedelta(days=start_offset),
                end_date=TODAY + timedelta(days=start_offset + duration),
                role_on_engagement=random.choice(["Lead", "Reviewer", "Executive", None]),
            )
            db.add(a)

        # ── Leaves ──
        leaves_data = [
            ("Rohan Patel",   TODAY + timedelta(days=10), TODAY + timedelta(days=12), LeaveType.vacation,  LeaveStatus.approved),
            ("Neha Gupta",    TODAY + timedelta(days=20), TODAY + timedelta(days=25), LeaveType.vacation,  LeaveStatus.approved),
            ("Karan Joshi",   TODAY + timedelta(days=5),  TODAY + timedelta(days=7),  LeaveType.sick,      LeaveStatus.pending),
            ("Anjali Mehta",  TODAY + timedelta(days=15), TODAY + timedelta(days=16), LeaveType.other,     LeaveStatus.pending),
            ("Meera Chopra",  TODAY + timedelta(days=30), TODAY + timedelta(days=35), LeaveType.vacation,  LeaveStatus.approved),
        ]
        for member_name, start, end, ltype, status in leaves_data:
            member = next(m for m in members if m.name == member_name)
            l = Leave(
                team_member_id=member.id,
                start_date=start, end_date=end,
                leave_type=ltype, status=status,
                reason="Personal" if ltype != LeaveType.sick else "Medical",
            )
            db.add(l)

        db.commit()
        print(f"Seeded {len(members)} team members, {len(CLIENTS)} clients, {len(ENGAGEMENTS)} engagements")
        print(f"Seeded {len(assignments_data)} assignments, {len(leaves_data)} leaves")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
