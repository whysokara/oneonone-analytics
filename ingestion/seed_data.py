"""
Seed realistic test data into Supabase across all 9 source tables.
Each run appends new rows — no dedup, no wipe.

Usage:
  python ingestion/seed_data.py           # append fresh rows
  python ingestion/seed_data.py --reset   # wipe all seed data then reseed clean
"""

import random
import string
import sys
import uuid
from datetime import datetime, timedelta, timezone

from db import get_supabase_client

# ── helpers ───────────────────────────────────────────────────────────────────

def tid():
    return str(uuid.uuid4())

def uid():
    return str(uuid.uuid4())

def now_utc():
    return datetime.now(timezone.utc)

def _parse_ts(ts_str):
    """Parse an ISO timestamp string to a timezone-aware datetime."""
    dt = datetime.fromisoformat(ts_str[:26])
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def rand_ts_after(after_ts_str, max_days_after=180):
    """Random ISO timestamp in the window (after_ts_str, after_ts_str + max_days_after].
    Capped at now — never produces a future timestamp."""
    after_dt = _parse_ts(after_ts_str)
    now = now_utc()
    if after_dt >= now:
        return now.isoformat()
    latest = min(after_dt + timedelta(days=max_days_after), now)
    delta = int((latest - after_dt).total_seconds())
    if delta <= 0:
        return now.isoformat()
    return (after_dt + timedelta(seconds=random.randint(0, delta))).isoformat()

def rand_date_after(after_str, max_days_after=180):
    """Random date string (YYYY-MM-DD) after the given date/timestamp string.
    Capped at today."""
    after_dt = _parse_ts(after_str[:10] + "T00:00:00+00:00")
    now = now_utc()
    latest = min(after_dt + timedelta(days=max_days_after), now)
    delta = (latest - after_dt).days
    if delta <= 0:
        return now.strftime("%Y-%m-%d")
    return (after_dt + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")

def today_ts():
    return now_utc().isoformat()

def today_date():
    return now_utc().strftime("%Y-%m-%d")

def invite_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def stamp_today(rows, ts_field=None, date_field=None):
    """Stamp today's date on the first row of every batch so runs are trackable.
    When setting createdAt to today, also sets updatedAt — they can never diverge."""
    if not rows:
        return rows
    ts = today_ts()
    if ts_field:
        rows[0][ts_field] = ts
        sibling = "updatedAt" if ts_field == "createdAt" else "updated_at"
        if sibling in rows[0]:
            rows[0][sibling] = ts
    if date_field:
        rows[0][date_field] = today_date()
        # entryDate = today means the work happened today → createdAt must be >= today
        if date_field == "entryDate" and "createdAt" in rows[0]:
            rows[0]["createdAt"] = ts
            rows[0]["updatedAt"] = ts
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

ENTRY_TEMPLATES = {
    "achievement": [
        ("Delivered authentication module ahead of schedule",
         "Completed the full OAuth2 integration two weeks before the deadline, enabling the mobile team to unblock their release."),
        ("Shipped the v2 onboarding flow on time",
         "Led the end-to-end build of the redesigned onboarding, coordinating across design, backend, and QA with no delays."),
    ],
    "impact": [
        ("Reduced API response time by 40%",
         "Profiled and optimized the main query bottleneck, improving P95 latency from 800ms to 480ms."),
        ("Cut deploy pipeline time from 18 min to 7 min",
         "Parallelized test jobs and removed redundant build steps. Teams now ship faster with higher confidence."),
    ],
    "learning": [
        ("Completed Kubernetes certification course",
         "Finished the 20-hour CKA prep course and passed all practice exams. Sitting the official exam next month."),
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
         "The CI pipeline has been intermittently failing for five days. Three teams are affected. Root cause under investigation."),
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
        # managers are the root — their signup date is the earliest anchor
        ts = (now_utc() - timedelta(days=random.randint(30, 365))).isoformat()
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
        # board created after the manager signed up
        ts = rand_ts_after(mgr["createdAt"], max_days_after=30)
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
            # reportee joined the board after the board was created
            ts = rand_ts_after(board["createdAt"], max_days_after=180)
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
                "joinedAt": ts,  # joined = same moment as account created
            })
    return reportee_rows, membership_rows


def gen_subscriptions(managers):
    rows = []
    for mgr in managers:
        plan    = pick(["free", "pro", "pro_plus"],                         [55, 30, 15])
        status  = pick(["active", "canceled", "past_due", "complimentary"], [75, 10, 10, 5])
        billing = pick(["monthly", "annual"],                               [70, 30])
        is_comp = status == "complimentary"
        # subscription created after manager signed up (within first 30 days)
        ts = rand_ts_after(mgr["createdAt"], max_days_after=30)
        # current_period_end: future for active, past for lapsed, null for complimentary
        if status == "active":
            period_end = (now_utc() + timedelta(days=random.randint(5, 365))).isoformat()
        elif status in ("canceled", "past_due"):
            period_end = (now_utc() - timedelta(days=random.randint(1, 90))).isoformat()
        else:
            period_end = None
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
    """
    memberships_by_board: {board_id: [(user_id, joined_at), ...]}
    managers_by_board:    {board_id: (manager_id, manager_created_at)}
    """
    categories = [
        "achievement", "impact", "learning", "recognition", "challenge",
        "certification", "positive_observation", "improvement_area",
        "coaching_note", "other", "discipline_issue",
        "project_contribution", "appreciation", "blocker", "issue",
    ]
    cat_weights = [28, 20, 14, 8, 7, 3, 3, 2, 1, 3, 2, 5, 4, 2, 2]

    rows = []
    for board in boards:
        members = memberships_by_board.get(board["id"], [])  # [(user_id, joined_at)]
        manager_id, manager_created_at = managers_by_board[board["id"]]
        if not members:
            continue

        total = random.randint(4, 12)
        n_self = random.randint(1, 2)

        # Self-entries: manager logs their own work (joinedAt = manager's signup date)
        for _ in range(n_self):
            rows.append(_build_entry(
                board["id"], manager_id, manager_id, manager_created_at,
                categories, cat_weights, is_self=True,
            ))

        # Team entries: one of the board's members logs work
        for _ in range(total - n_self):
            member_id, joined_at = random.choice(members)
            rows.append(_build_entry(
                board["id"], member_id, member_id, joined_at,
                categories, cat_weights, is_self=False,
            ))

    return rows


def _build_entry(board_id, employee_id, created_by, joined_at, categories, weights, is_self):
    category = pick(categories, weights)
    title, desc = random.choice(ENTRY_TEMPLATES[category])
    status = pick(["draft", "pending_approval", "published"], [20, 20, 60])

    # entryDate = when the work happened (after employee joined, up to 150 days later)
    entry_date = rand_date_after(joined_at, max_days_after=150)
    # createdAt = when it was logged — after or on entryDate (people log work after it happens)
    created_ts = rand_ts_after(entry_date + "T00:00:00+00:00", max_days_after=14)
    updated_ts = created_ts

    entry = {
        "id": tid(),
        "boardId": board_id,
        "employeeId": employee_id,
        "createdByUserId": created_by,
        "visibility": pick(["shared", "manager_private"], [75, 25]),
        "category": category,
        "title": title,
        "description": desc,
        "entryDate": entry_date,
        "createdAt": created_ts,
        "updatedAt": updated_ts,
        "status": status,
    }
    if category == "certification" and random.random() < 0.5:
        entry["certificationUrl"] = random.choice(CERT_URLS)
    if random.random() < 0.30:
        entry["goalTag"] = random.choice(GOAL_TAGS)
    if status == "published" and not is_self and random.random() < 0.20:
        entry["managerNote"] = random.choice(MANAGER_NOTES)
        # manager added the note some time after the entry was created
        entry["updatedAt"] = rand_ts_after(created_ts, max_days_after=14)
    return entry


def gen_announcements(boards, managers_by_board):
    rows = []
    for board in boards:
        manager_id, _ = managers_by_board[board["id"]]
        for _ in range(random.randint(1, 3)):
            title, message = random.choice(ANNOUNCEMENT_TEMPLATES)
            # announcement posted after the board was created
            ts = rand_ts_after(board["createdAt"], max_days_after=150)
            rows.append({
                "id": tid(),
                "boardId": board["id"],
                "createdByUserId": manager_id,
                "title": title,
                "message": message,
                "createdAt": ts,
                "updatedAt": ts,
            })
    return rows


def gen_support_requests(users_with_ts):
    """users_with_ts: [(user_id, created_at), ...]"""
    rows = []
    for _ in range(random.randint(2, 5)):
        req_type = random.choice(["bug", "feature", "support"])
        user_id, user_created_at = random.choice(users_with_ts)
        rows.append({
            "id": tid(),
            "userId": user_id,
            "type": req_type,
            "message": random.choice(SUPPORT_TEMPLATES[req_type]),
            # request submitted after the user account existed
            "createdAt": rand_ts_after(user_created_at, max_days_after=90),
        })
    return rows


def gen_usage_events(users_with_ts):
    """users_with_ts: [(user_id, created_at), ...]"""
    rows = []
    for _ in range(random.randint(3, 8)):
        user_id, user_created_at = random.choice(users_with_ts)
        rows.append({
            "id": uid(),
            "user_id": user_id,
            "feature": "ai_summary",
            # event fired after the user account existed
            "created_at": rand_ts_after(user_created_at, max_days_after=90),
        })
    return rows

# ── cleanup ───────────────────────────────────────────────────────────────────

def cleanup_seed_data(client):
    """Delete all rows seeded by this script (identified by seed.* email pattern)."""
    print("[cleanup] Finding seed users...")
    result = client.table("users").select("id,role").like("email", "seed.%@example.com").execute()
    if not result.data:
        print("[cleanup] No seed data found — nothing to clean.")
        return

    all_ids  = [r["id"] for r in result.data]
    mgr_ids  = [r["id"] for r in result.data if r["role"] == "manager"]

    board_ids = []
    if mgr_ids:
        b = client.table("boards").select("id").in_("managerId", mgr_ids).execute()
        board_ids = [r["id"] for r in b.data]

    # delete dependents first (FK order)
    if board_ids:
        client.table("entries").delete().in_("boardId", board_ids).execute()
        client.table("memberships").delete().in_("boardId", board_ids).execute()
        client.table("announcements").delete().in_("boardId", board_ids).execute()
    if all_ids:
        client.table("subscriptions").delete().in_("user_id", all_ids).execute()
        client.table("support_requests").delete().in_("userId", all_ids).execute()
        client.table("usage_events").delete().in_("user_id", all_ids).execute()
    if board_ids:
        client.table("boards").delete().in_("id", board_ids).execute()
    if all_ids:
        client.table("users").delete().in_("id", all_ids).execute()

    # remove from Supabase Auth
    deleted_auth = 0
    for user_id in all_ids:
        try:
            client.auth.admin.delete_user(user_id)
            deleted_auth += 1
        except Exception as e:
            print(f"[cleanup] Warning: could not delete auth user {user_id}: {e}")

    print(f"[cleanup] Removed {len(all_ids)} seed users ({deleted_auth} auth records) "
          f"and all related rows across 7 tables.")

# ── insert helper ─────────────────────────────────────────────────────────────

def insert(client, table, rows):
    if not rows:
        return 0
    if table == "users":
        client.table(table).upsert(rows, on_conflict="id").execute()
    else:
        client.table(table).insert(rows).execute()
    return len(rows)

# ── main ──────────────────────────────────────────────────────────────────────

def run():
    client = get_supabase_client()
    counts = {}

    # 1. Managers
    managers = stamp_today(gen_managers(client, random.randint(2, 4)), ts_field="createdAt")
    counts["users (managers)"] = insert(client, "users", managers)

    # 2. Boards — created after their manager
    boards = stamp_today(gen_boards(managers), ts_field="createdAt")
    counts["boards"] = insert(client, "boards", boards)

    # board_id → (manager_id, manager_created_at)
    mgr_lookup = {m["id"]: m["createdAt"] for m in managers}
    managers_by_board = {b["id"]: (b["managerId"], mgr_lookup[b["managerId"]]) for b in boards}

    # 3. Reportees + memberships — joined after their board was created
    reportees, memberships = gen_reportees_and_memberships(client, boards)
    stamp_today(reportees, ts_field="createdAt")
    stamp_today(memberships, ts_field="joinedAt")
    counts["users (reportees)"] = insert(client, "users", reportees)
    counts["memberships"] = insert(client, "memberships", memberships)

    # board_id → [(user_id, joined_at)]
    memberships_by_board = {}
    for m in memberships:
        memberships_by_board.setdefault(m["boardId"], []).append((m["userId"], m["joinedAt"]))

    # 4. Subscriptions — created after manager signed up
    subs = stamp_today(gen_subscriptions(managers), ts_field="created_at")
    counts["subscriptions"] = insert(client, "subscriptions", subs)

    # 5. Entries — entryDate after employee joined; createdAt after entryDate
    entries = stamp_today(gen_entries(boards, memberships_by_board, managers_by_board), date_field="entryDate")
    counts["entries"] = insert(client, "entries", entries)

    # 6. Announcements — posted after board was created
    announcements = stamp_today(gen_announcements(boards, managers_by_board), ts_field="createdAt")
    counts["announcements"] = insert(client, "announcements", announcements)

    # 7. Support requests + usage events — after the user's account existed
    all_users_with_ts = (
        [(u["id"], u["createdAt"]) for u in managers] +
        [(u["id"], u["createdAt"]) for u in reportees]
    )
    support = stamp_today(gen_support_requests(all_users_with_ts), ts_field="createdAt")
    counts["support_requests"] = insert(client, "support_requests", support)

    usage = stamp_today(gen_usage_events(all_users_with_ts), ts_field="created_at")
    counts["usage_events"] = insert(client, "usage_events", usage)

    print("\nSeed run complete:")
    for table, count in counts.items():
        print(f"  {table:<30} +{count} rows")


if __name__ == "__main__":
    client = get_supabase_client()
    if "--reset" in sys.argv:
        cleanup_seed_data(client)
    run()
