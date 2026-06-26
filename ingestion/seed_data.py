"""
Seed realistic test data into Supabase across all 9 source tables.
Each run appends new rows — no dedup, no wipe.
Run: python ingestion/seed_data.py
"""

import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from db import get_supabase_client

# ── helpers ───────────────────────────────────────────────────────────────────

def tid():
    return str(uuid.uuid4())

def uid():
    return str(uuid.uuid4())

def rand_past_ts(max_days=180):
    offset = random.randint(0, max_days)
    dt = datetime.now(timezone.utc) - timedelta(days=offset)
    return dt.isoformat()

def rand_past_date(max_days=180):
    offset = random.randint(0, max_days)
    dt = datetime.now(timezone.utc) - timedelta(days=offset)
    return dt.strftime("%Y-%m-%d")

def invite_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def today_ts():
    return datetime.now(timezone.utc).isoformat()

def today_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def stamp_today(rows, ts_field=None, date_field=None):
    """Set today's date on the first row so every run is trackable by date."""
    if not rows:
        return rows
    if ts_field:
        rows[0][ts_field] = today_ts()
    if date_field:
        rows[0][date_field] = today_date()
    return rows

def pick(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

# ── data pools ────────────────────────────────────────────────────────────────

FULL_NAMES = [
    "Priya Sharma", "Rohan Mehta", "Ananya Patel", "Vikram Singh", "Neha Gupta",
    "Arjun Kumar", "Kavya Reddy", "Siddharth Joshi", "Divya Nair", "Rahul Verma",
    "Sarah Chen", "Michael Park", "Emma Wilson", "James Rodriguez", "Olivia Thompson",
    "Liam Anderson", "Sofia Martinez", "Noah Johnson", "Isabella Davis", "Ethan Brown",
    "Aarav Kapoor", "Meera Iyer", "Kiran Rao", "Deepak Agarwal", "Pooja Srivastava",
    "Alex Lee", "Jordan Taylor", "Morgan Williams", "Casey Jones", "Riley Smith",
]

ORG_NAMES = [
    "Nexora Labs", "Brightwave Technologies", "Pinnacle Solutions", "Orion Digital",
    "Craft & Code", "Vertex Systems", "Sparrow Analytics", "Luminary Group",
    "Delta Force Tech", "Zenith Innovations",
]

JOB_TITLES = [
    "Software Engineer", "Product Manager", "UX Designer", "Data Analyst",
    "Marketing Lead", "Sales Executive", "DevOps Engineer", "QA Engineer",
    "Frontend Developer", "Backend Engineer",
]

BOARD_NAMES = [
    "Engineering Team", "Design & UX", "Product Team", "Sales Squad",
    "Marketing Crew", "Data & Analytics", "Platform Team", "Growth Team",
    "Customer Success", "Operations",
]

BOARD_DESCRIPTIONS = [
    "Tracking progress, wins, and growth for our core engineering squad.",
    "A space for design insights, creative wins, and UX feedback.",
    "Product team entries covering feature launches, decisions, and learnings.",
    "Sales team performance tracking and client relationship notes.",
    "Marketing initiatives, campaign outcomes, and growth experiments.",
    "Data work, analysis outputs, and pipeline improvements.",
    "Platform reliability, infrastructure improvements, and system health.",
    "Growth experiments, funnel metrics, and hypothesis outcomes.",
    "Customer success stories, escalations resolved, and NPS improvements.",
    "Operational efficiency wins and process improvement notes.",
]

# 2 templates per category — randomly chosen per entry
ENTRY_TEMPLATES = {
    "achievement": [
        ("Delivered authentication module ahead of schedule",
         "Completed the full OAuth2 integration two weeks before the deadline, enabling the mobile team to unblock their release."),
        ("Shipped the v2 onboarding flow on time",
         "Led the end-to-end build of the redesigned onboarding, coordinating across design, backend, and QA with no delays."),
    ],
    "impact": [
        ("Reduced API response time by 40%",
         "Profiled and optimized the main query bottleneck in the reporting service, improving P95 latency from 800ms to 480ms."),
        ("Cut deploy pipeline time from 18 min to 7 min",
         "Parallelized test jobs and removed redundant build steps. Teams now ship faster with higher confidence."),
    ],
    "learning": [
        ("Completed Kubernetes certification course",
         "Finished the 20-hour CKA prep course and passed all practice exams. Planning to sit the official exam next month."),
        ("Deep-dived into event-driven architecture patterns",
         "Built a proof-of-concept Kafka consumer to understand how async workflows differ from REST."),
    ],
    "recognition": [
        ("Client commendation for go-live support",
         "Stayed on-call for 48 hours during the client's production go-live and resolved three critical issues in real time."),
        ("Called out in all-hands for cross-team collaboration",
         "Led a complex migration across four teams with zero production incidents. Recognised by leadership."),
    ],
    "challenge": [
        ("Navigating unclear product requirements",
         "Spent two sprints on a feature with shifting acceptance criteria. Working with PM to tighten the definition-of-done."),
        ("Inherited a poorly documented legacy service",
         "Took ownership of a critical service with no runbook and outdated comments. First two weeks were just mapping the codebase."),
    ],
    "certification": [
        ("AWS Solutions Architect – Associate certified",
         "Passed the AWS SAA-C03 exam on first attempt. Certificate valid through 2027."),
        ("Google Professional Data Engineer certified",
         "Cleared the GCP Data Engineer exam after six weeks of prep. Covers BigQuery, Dataflow, and Pub/Sub in depth."),
    ],
    "positive_observation": [
        ("Proactive cross-team sync during the redesign",
         "Set up sync sessions with the backend team without being asked. The integration went smoothly as a direct result."),
        ("Consistently thorough PR reviews",
         "Every review includes context, not just comments. Junior engineers have specifically called this out as helpful."),
    ],
    "improvement_area": [
        ("Documentation habits need improvement",
         "Code contributions are strong but docs are often missing or outdated. Agreed to make documentation part of every PR."),
        ("Estimation accuracy is inconsistent",
         "Three of the last five tasks went significantly over estimate. Will start breaking work into smaller units."),
    ],
    "coaching_note": [
        ("Career growth conversation: senior to staff path",
         "Discussed the path from senior to staff. Agreed on a 6-month plan focused on cross-team influence and system design."),
        ("1:1 check-in on sustainable work pace",
         "Flagged signs of overwork during the last sprint. Agreed on clearer sprint scope limits going forward."),
    ],
    "other": [
        ("Onboarded two new junior engineers",
         "Led onboarding for two new hires — prepared materials, ran 1:1 sessions, helped them ship their first PRs."),
        ("Facilitated the quarterly retrospective",
         "Used the 4Ls framework. Generated 12 actionable items, 8 of which are now in the backlog."),
    ],
    "discipline_issue": [
        ("Attendance and punctuality concern",
         "Third missed standup this quarter without prior notice. Had a direct conversation about expectations."),
        ("Code review SLA repeatedly missed",
         "Reviews left open for 4+ days three times. Agreed on a 24-hour SLA going forward."),
    ],
    "project_contribution": [
        ("Led backend integration for the payments module",
         "Owned the Stripe integration end-to-end across three sprints. Coordinated with frontend and QA throughout."),
        ("Contributed key features to the new mobile release",
         "Shipped four features in the mobile v2 release, including offline mode and push notifications."),
    ],
    "appreciation": [
        ("Thank you for covering during my leave",
         "Stepped up to own two critical incidents while I was on leave. The team felt fully supported."),
        ("Outstanding help during the product launch",
         "Went above and beyond during the launch weekend — available at short notice, calm under pressure."),
    ],
    "blocker": [
        ("Blocked on design sign-off for three weeks",
         "The feature spec has been ready but no design review has been scheduled. Escalated to the PM this week."),
        ("Dependency on the data team is delaying the milestone",
         "Waiting on a schema change from the data team since sprint start. Raised in the last planning session."),
    ],
    "issue": [
        ("Production bug caused data inconsistency in reports",
         "A race condition in the aggregation job resulted in incorrect numbers for two customers. Hotfix deployed."),
        ("Deployment pipeline flaky — blocking two teams",
         "The CI pipeline has been intermittently failing for five days. Three teams are affected. Root cause still under investigation."),
    ],
}

GOAL_TAGS = [
    "OKR-Q1: Improve system reliability",
    "Goal: Launch mobile v2",
    "OKR-Q2: Grow team efficiency",
    "Goal: Reduce time-to-deploy",
    "Initiative: Customer satisfaction",
    "OKR-Q3: Expand platform capabilities",
    "Goal: Zero-downtime deploys",
    "Initiative: Documentation overhaul",
]

MANAGER_NOTES = [
    "Great progress this quarter. Keep it up.",
    "Discussed in our 1:1. Agreed on next steps.",
    "Highlighted this in the team review — excellent work.",
    "Good example of the initiative we want to see more of.",
    "We'll revisit this in the next performance cycle.",
    "Flagged as a growth area to watch.",
]

ANNOUNCEMENT_TEMPLATES = [
    ("Q2 Team Goals Published",
     "The Q2 OKR document is now live. Please review and add your key results by end of week."),
    ("New Process: Entry Review Cycle",
     "Starting next month, all entries require manager review within 5 business days of submission."),
    ("Team milestone reached — great work!",
     "We hit our entry logging milestone this month. Incredible effort from everyone — keep it going!"),
    ("Reminder: Catch up on outstanding entries",
     "A few team members have entries from last month still pending. Please log them before the freeze date."),
    ("Welcome to the new team members",
     "Please join me in welcoming the two new engineers who joined us this week. Reach out and say hi!"),
]

SUPPORT_TEMPLATES = {
    "bug": [
        "The entry submission form throws a 500 error when I try to attach a certification URL.",
        "Unable to log in after resetting my password — keeps saying 'invalid credentials'.",
    ],
    "feature": [
        "Would love the ability to export my entries to PDF for performance reviews.",
        "Can we add a bulk-approve option for managers reviewing pending entries?",
    ],
    "support": [
        "I was charged twice this month. Please help me get a refund for the duplicate charge.",
        "Quick question — does the entry date affect how metrics are calculated?",
    ],
}

CERT_URLS = [
    "https://www.credly.com/badges/example-aws-saa",
    "https://www.credly.com/badges/example-gcp-pde",
    "https://learn.microsoft.com/en-us/certifications/example",
    "https://www.coursera.org/account/accomplishments/example",
]

# ── generators ────────────────────────────────────────────────────────────────

def create_auth_user(client, email):
    # public.users.id has a FK → auth.users(id), so we must create the auth user first
    # and use the returned ID. email_confirm=True skips the confirmation email.
    resp = client.auth.admin.create_user({
        "email": email,
        "password": "Seed@Data#2024!",
        "email_confirm": True,
    })
    return str(resp.user.id)


def gen_managers(client, n):
    rows = []
    for name in random.sample(FULL_NAMES, min(n, len(FULL_NAMES))):
        slug = name.lower().replace(" ", ".")
        email = f"seed.mgr.{slug}.{uuid.uuid4().hex[:4]}@example.com"
        auth_id = create_auth_user(client, email)
        ts = rand_past_ts(max_days=365)
        rows.append({
            "id": auth_id,
            "authUserId": auth_id,
            "fullName": name,
            "email": email,
            "role": "manager",
            "createdAt": ts,
            "updatedAt": ts,
            "orgName": random.choice(ORG_NAMES) if random.random() < 0.7 else None,
            "jobTitle": "Engineering Manager" if random.random() < 0.5 else random.choice(JOB_TITLES),
        })
    return rows


def gen_boards(managers):
    rows = []
    for mgr in managers:
        idx = random.randint(0, len(BOARD_NAMES) - 1)
        ts = rand_past_ts(max_days=300)
        rows.append({
            "id": tid(),
            "managerId": mgr["id"],
            "name": BOARD_NAMES[idx],
            "description": BOARD_DESCRIPTIONS[idx],
            "inviteCode": invite_code(),
            "createdAt": ts,
            "updatedAt": ts,
        })
    return rows


def gen_reportees_and_memberships(client, boards):
    reportee_rows = []
    membership_rows = []
    for board in boards:
        n = random.randint(3, 8)
        for name in random.sample(FULL_NAMES, min(n, len(FULL_NAMES))):
            slug = name.lower().replace(" ", ".")
            email = f"seed.rep.{slug}.{uuid.uuid4().hex[:4]}@example.com"
            auth_id = create_auth_user(client, email)
            ts = rand_past_ts(max_days=280)
            reportee_rows.append({
                "id": auth_id,
                "authUserId": auth_id,
                "fullName": name,
                "email": email,
                "role": "reportee",
                "createdAt": ts,
                "updatedAt": ts,
                "jobTitle": random.choice(JOB_TITLES) if random.random() < 0.6 else None,
            })
            membership_rows.append({
                "id": tid(),
                "boardId": board["id"],
                "userId": auth_id,
                "joinedAt": ts,
            })
    return reportee_rows, membership_rows


def gen_subscriptions(managers):
    rows = []
    for mgr in managers:
        plan    = pick(["free", "pro", "pro_plus"],         [55, 30, 15])
        status  = pick(["active", "canceled", "past_due", "complimentary"], [75, 10, 10, 5])
        billing = pick(["monthly", "annual"],               [70, 30])
        is_comp = status == "complimentary"
        ts = rand_past_ts(max_days=300)
        period_end = None
        if status == "active":
            period_end = (
                datetime.now(timezone.utc) + timedelta(days=random.randint(5, 365))
            ).isoformat()
        rows.append({
            "id": tid(),
            "user_id": mgr["id"],
            "plan": plan,
            "billing_cycle": billing,
            "status": status,
            "is_complimentary": is_comp,
            "current_period_end": period_end,
            "created_at": ts,
            "updated_at": ts,
        })
    return rows


def gen_entries(boards, memberships_by_board, managers_by_board):
    categories = [
        "achievement", "impact", "learning", "recognition", "challenge",
        "certification", "positive_observation", "improvement_area",
        "coaching_note", "other", "discipline_issue",
        "project_contribution", "appreciation", "blocker", "issue",
    ]
    # mirrors approximate real prod distribution (achievement heaviest)
    cat_weights = [28, 20, 14, 8, 7, 3, 3, 2, 1, 3, 2, 5, 4, 2, 2]

    rows = []
    for board in boards:
        members = memberships_by_board.get(board["id"], [])
        manager_id = managers_by_board[board["id"]]
        if not members:
            continue

        total = random.randint(4, 12)
        n_self = random.randint(1, 2)

        # Manager self-entries (employeeId = managerId)
        for _ in range(n_self):
            rows.append(_build_entry(board["id"], manager_id, manager_id, categories, cat_weights, is_self=True))

        # Team entries from reportees
        for _ in range(total - n_self):
            member_id = random.choice(members)
            rows.append(_build_entry(board["id"], member_id, member_id, categories, cat_weights, is_self=False))

    return rows


def _build_entry(board_id, employee_id, created_by, categories, weights, is_self):
    category = pick(categories, weights)
    title, desc = random.choice(ENTRY_TEMPLATES[category])
    status = pick(["draft", "pending_approval", "published"], [20, 20, 60])
    ts = rand_past_ts()
    entry = {
        "id": tid(),
        "boardId": board_id,
        "employeeId": employee_id,
        "createdByUserId": created_by,
        "visibility": pick(["shared", "manager_private"], [75, 25]),
        "category": category,
        "title": title,
        "description": desc,
        "entryDate": rand_past_date(),
        "createdAt": ts,
        "updatedAt": ts,
        "status": status,
    }
    if category == "certification" and random.random() < 0.5:
        entry["certificationUrl"] = random.choice(CERT_URLS)
    if random.random() < 0.30:
        entry["goalTag"] = random.choice(GOAL_TAGS)
    if status == "published" and not is_self and random.random() < 0.20:
        entry["managerNote"] = random.choice(MANAGER_NOTES)
    return entry


def gen_announcements(boards, managers_by_board):
    rows = []
    for board in boards:
        for _ in range(random.randint(1, 3)):
            title, message = random.choice(ANNOUNCEMENT_TEMPLATES)
            ts = rand_past_ts()
            rows.append({
                "id": tid(),
                "boardId": board["id"],
                "createdByUserId": managers_by_board[board["id"]],
                "title": title,
                "message": message,
                "createdAt": ts,
                "updatedAt": ts,
            })
    return rows



def gen_support_requests(all_user_ids):
    types = ["bug", "feature", "support"]
    rows = []
    for _ in range(random.randint(2, 5)):
        req_type = random.choice(types)
        rows.append({
            "id": tid(),
            "userId": random.choice(all_user_ids),
            "type": req_type,
            "message": random.choice(SUPPORT_TEMPLATES[req_type]),
            "createdAt": rand_past_ts(max_days=90),
        })
    return rows


def gen_usage_events(all_user_ids):
    rows = []
    for _ in range(random.randint(3, 8)):
        rows.append({
            "id": uid(),
            "user_id": random.choice(all_user_ids),
            "feature": "ai_summary",
            "created_at": rand_past_ts(max_days=90),
        })
    return rows

# ── insert helper ─────────────────────────────────────────────────────────────

def insert(client, table, rows):
    if not rows:
        return 0
    # users: upsert in case a DB trigger already created the profile row from auth
    if table == "users":
        client.table(table).upsert(rows, on_conflict="id").execute()
    else:
        client.table(table).insert(rows).execute()
    return len(rows)

# ── main ──────────────────────────────────────────────────────────────────────

def run():
    client = get_supabase_client()
    counts = {}

    # 1. Managers (creates auth users + public profiles)
    managers = stamp_today(gen_managers(client, random.randint(2, 4)), ts_field="createdAt")
    counts["users (managers)"] = insert(client, "users", managers)

    # 2. Boards (depends on managers)
    boards = stamp_today(gen_boards(managers), ts_field="createdAt")
    counts["boards"] = insert(client, "boards", boards)

    managers_by_board = {b["id"]: b["managerId"] for b in boards}

    # 3. Reportees + memberships (depends on boards)
    reportees, memberships = gen_reportees_and_memberships(client, boards)
    stamp_today(reportees, ts_field="createdAt")
    stamp_today(memberships, ts_field="joinedAt")
    counts["users (reportees)"] = insert(client, "users", reportees)
    counts["memberships"] = insert(client, "memberships", memberships)

    memberships_by_board = {}
    for m in memberships:
        memberships_by_board.setdefault(m["boardId"], []).append(m["userId"])

    # 4. Subscriptions (depends on managers)
    subs = stamp_today(gen_subscriptions(managers), ts_field="created_at")
    counts["subscriptions"] = insert(client, "subscriptions", subs)

    # 5. Entries (depends on boards + members)
    # stamp entryDate (the business date MetricFlow uses) so metrics show today's activity
    entries = stamp_today(gen_entries(boards, memberships_by_board, managers_by_board), date_field="entryDate")
    counts["entries"] = insert(client, "entries", entries)

    # 6. Announcements (depends on boards + managers)
    announcements = stamp_today(gen_announcements(boards, managers_by_board), ts_field="createdAt")
    counts["announcements"] = insert(client, "announcements", announcements)

    # 7. Support requests
    all_user_ids = [u["id"] for u in managers + reportees]
    support = stamp_today(gen_support_requests(all_user_ids), ts_field="createdAt")
    counts["support_requests"] = insert(client, "support_requests", support)

    # 8. Usage events
    usage = stamp_today(gen_usage_events(all_user_ids), ts_field="created_at")
    counts["usage_events"] = insert(client, "usage_events", usage)

    print("\nSeed run complete:")
    for table, count in counts.items():
        print(f"  {table:<30} +{count} rows")


if __name__ == "__main__":
    run()
