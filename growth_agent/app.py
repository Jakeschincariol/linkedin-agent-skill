"""Approval-first LinkedIn growth workspace (Python standard library only)."""
from __future__ import annotations
import argparse, csv, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.environ.get("LINKEDIN_AGENT_DB", "data/linkedin_agent.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS drafts (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
 scheduled_for TEXT, status TEXT NOT NULL DEFAULT 'draft'
 CHECK(status IN ('draft','approved','published','archived')),
 approved_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, organization TEXT, role TEXT,
 category TEXT NOT NULL DEFAULT 'peer', email TEXT, linkedin_url TEXT,
 location TEXT, source TEXT, notes TEXT, status TEXT NOT NULL DEFAULT 'identified',
 last_contact_at TEXT, next_follow_up TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS touchpoints (
 id INTEGER PRIMARY KEY, contact_id INTEGER NOT NULL REFERENCES contacts(id),
 channel TEXT NOT NULL, direction TEXT NOT NULL DEFAULT 'outbound',
 summary TEXT NOT NULL, occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS post_metrics (
 id INTEGER PRIMARY KEY, post_ref TEXT NOT NULL, captured_at TEXT NOT NULL,
 impressions INTEGER DEFAULT 0, reactions INTEGER DEFAULT 0,
 comments INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0,
 UNIQUE(post_ref,captured_at)
);
"""

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def add_draft(title, body, scheduled_for=None):
    if not title.strip() or not body.strip(): raise ValueError("title and body are required")
    if scheduled_for:
        datetime.fromisoformat(scheduled_for.replace("Z","+00:00"))
    with connect() as c:
        cur=c.execute("INSERT INTO drafts(title,body,scheduled_for,created_at) VALUES(?,?,?,?)",
                      (title.strip(),body.strip(),scheduled_for,now()))
        return cur.lastrowid

def approve_draft(draft_id):
    with connect() as c:
        cur=c.execute("UPDATE drafts SET status='approved',approved_at=? WHERE id=? AND status='draft'",
                      (now(),draft_id))
        if cur.rowcount != 1: raise ValueError("Draft not found or not in draft state")
    return draft_id

def add_contact(name, category="peer", organization=None, role=None, email=None,
                linkedin_url=None, location=None, source=None, notes=None, next_follow_up=None):
    if not name.strip(): raise ValueError("contact name is required")
    with connect() as c:
        cur=c.execute("""INSERT INTO contacts(name,category,organization,role,email,linkedin_url,
        location,source,notes,next_follow_up,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (name.strip(),category,organization,role,email,linkedin_url,location,source,notes,next_follow_up,now()))
        return cur.lastrowid

def log_touch(contact_id, channel, summary, direction="outbound"):
    with connect() as c:
        if not c.execute("SELECT 1 FROM contacts WHERE id=?",(contact_id,)).fetchone():
            raise ValueError("contact not found")
        c.execute("INSERT INTO touchpoints(contact_id,channel,direction,summary,occurred_at) VALUES(?,?,?,?,?)",
                  (contact_id,channel,direction,summary,now()))
        if direction == "outbound":
            c.execute("UPDATE contacts SET last_contact_at=? WHERE id=?",(now(),contact_id))

def import_metrics(csv_path):
    required={"post_ref","captured_at","impressions","reactions","comments","reposts","clicks"}
    count=0
    with open(csv_path,newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV requires columns: "+", ".join(sorted(required)))
        with connect() as c:
            for row in reader:
                vals=[row[k] for k in ("post_ref","captured_at")]
                nums=[int(row[k] or 0) for k in ("impressions","reactions","comments","reposts","clicks")]
                if any(n < 0 for n in nums): raise ValueError("metrics cannot be negative")
                c.execute("""INSERT INTO post_metrics(post_ref,captured_at,impressions,reactions,comments,reposts,clicks)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(post_ref,captured_at) DO UPDATE SET
                impressions=excluded.impressions,reactions=excluded.reactions,comments=excluded.comments,
                reposts=excluded.reposts,clicks=excluded.clicks""",(*vals,*nums))
                count+=1
    return count

def report():
    with connect() as c:
        drafts=c.execute("SELECT status,COUNT(*) n FROM drafts GROUP BY status").fetchall()
        contacts=c.execute("SELECT category,status,COUNT(*) n FROM contacts GROUP BY category,status").fetchall()
        m=c.execute("""SELECT COUNT(*) posts,COALESCE(SUM(impressions),0) impressions,
        COALESCE(SUM(reactions),0) reactions,COALESCE(SUM(comments),0) comments,
        COALESCE(SUM(reposts),0) reposts,COALESCE(SUM(clicks),0) clicks FROM post_metrics""").fetchone()
    return {"drafts":{r["status"]:r["n"] for r in drafts},
            "contacts":[dict(r) for r in contacts],"metrics":dict(m)}

def main():
    p=argparse.ArgumentParser(prog="linkedin-growth",description="Local-first, approval-first LinkedIn workflow")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("init")
    d=sub.add_parser("draft"); d.add_argument("title"); d.add_argument("body"); d.add_argument("--schedule")
    a=sub.add_parser("approve"); a.add_argument("id",type=int)
    c=sub.add_parser("contact"); c.add_argument("name"); c.add_argument("--category",default="peer")
    c.add_argument("--organization"); c.add_argument("--role"); c.add_argument("--email")
    c.add_argument("--linkedin-url"); c.add_argument("--location"); c.add_argument("--source")
    c.add_argument("--notes"); c.add_argument("--follow-up")
    t=sub.add_parser("touch"); t.add_argument("contact_id",type=int); t.add_argument("channel")
    t.add_argument("summary"); t.add_argument("--direction",default="outbound",choices=["outbound","inbound"])
    i=sub.add_parser("import-metrics"); i.add_argument("csv")
    sub.add_parser("report")
    args=p.parse_args()
    try:
        if args.cmd=="init": connect().close(); print(f"Initialized {DB}")
        elif args.cmd=="draft": print(f"Created draft #{add_draft(args.title,args.body,args.schedule)}")
        elif args.cmd=="approve": print(f"Approved draft #{approve_draft(args.id)} for manual publication")
        elif args.cmd=="contact":
            fields={k:getattr(args,k) for k in ("organization","role","email","linkedin_url","location","source","notes")}
            print(f"Created contact #{add_contact(args.name,args.category,**fields,next_follow_up=args.follow_up)}")
        elif args.cmd=="touch": log_touch(args.contact_id,args.channel,args.summary,args.direction); print("Touchpoint recorded")
        elif args.cmd=="import-metrics": print(f"Imported/updated {import_metrics(args.csv)} metric rows")
        elif args.cmd=="report":
            import json; print(json.dumps(report(),indent=2))
    except (ValueError, OSError) as exc:
        p.error(str(exc))

if __name__=="__main__": main()
