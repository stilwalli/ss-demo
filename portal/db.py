#!/usr/bin/env python3
"""Database management and seeding for State Street Mock Data Portal."""

import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "statestreet.db"
MOCK_DATA_PATH = Path("/usr/local/google/home/stilwalli/mywork/statestreet_research/statestreet_mock_data.json")
AUTH_DATA_PATH = Path("/usr/local/google/home/stilwalli/mywork/statestreet_research/auth_mock_data.json")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reseed=False):
    """Initializes the database schema and seeds with mock data if empty or forced."""
    conn = get_db_connection()
    cur = conn.cursor()

    if force_reseed:
        cur.execute("DROP TABLE IF EXISTS accounts")
        cur.execute("DROP TABLE IF EXISTS trades")
        cur.execute("DROP TABLE IF EXISTS work_items")
        cur.execute("DROP TABLE IF EXISTS bank_rec")

    # 1. Accounts Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_no TEXT PRIMARY KEY,
        auth_profile_id TEXT,
        investor_name TEXT,
        account_name TEXT,
        account_status TEXT,
        registered_email TEXT,
        registered_phone TEXT,
        phone_verified TEXT,
        allowed_otp_route TEXT,
        eligibility_note TEXT
    )
    """)

    # 2. Trades Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_ref TEXT PRIMARY KEY,
        account_no TEXT,
        fund_name TEXT,
        fund_code TEXT,
        trade_type TEXT,
        gross_amount REAL,
        currency TEXT,
        trade_status TEXT,
        trade_date TEXT,
        settlement_date TEXT,
        scenario TEXT
    )
    """)

    # 3. Work Items Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS work_items (
        work_item_id TEXT PRIMARY KEY,
        trade_ref TEXT,
        account_no TEXT,
        queue_name TEXT,
        sub_queue TEXT,
        work_item_status TEXT,
        nigo_reason TEXT,
        action_needed TEXT,
        sla TEXT,
        message TEXT,
        scenario TEXT
    )
    """)

    # 4. Bank Reconciliation Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bank_rec (
        trade_ref TEXT PRIMARY KEY,
        account_no TEXT,
        bank_rec_status TEXT,
        zilo_status TEXT,
        amount REAL,
        currency TEXT,
        subnr_flag TEXT,
        settlement_date TEXT,
        scenario TEXT
    )
    """)
    conn.commit()

    # Check if empty
    cur.execute("SELECT count(*) FROM accounts")
    count = cur.fetchone()[0]
    if count == 0 or force_reseed:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    """Seeds the database from JSON files."""
    cur = conn.cursor()

    # Load JSON files
    auth_data = {}
    if AUTH_DATA_PATH.exists():
        with open(AUTH_DATA_PATH) as f:
            auth_data = json.load(f)

    base_data = {}
    if MOCK_DATA_PATH.exists():
        with open(MOCK_DATA_PATH) as f:
            base_data = json.load(f)

    # Map Auth Profiles
    auth_profiles = {p.get("Account No"): p for p in auth_data.get("Authentication Profiles", [])}

    # Seed Accounts (28 accounts from base_data + 7 from auth_data)
    accounts = base_data.get("Accounts", [])
    for acc in accounts:
        acct_no = acc.get("Account No")
        ap = auth_profiles.get(acct_no, {})
        cur.execute("""
        INSERT OR REPLACE INTO accounts (
            account_no, auth_profile_id, investor_name, account_name,
            account_status, registered_email, registered_phone, phone_verified,
            allowed_otp_route, eligibility_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            acct_no,
            ap.get("Auth Profile ID", f"AUTH-{acct_no[-4:]}"),
            ap.get("Investor Name") or acc.get("Investor Name"),
            acc.get("Account Name"),
            ap.get("Account Status") or acc.get("Status", "Active"),
            ap.get("Registered Email") or acc.get("Investor Email"),
            ap.get("Registered Phone", "+1-617-555-0100"),
            ap.get("Phone Verified", "Yes"),
            ap.get("Allowed OTP Route", "Email OTP; SMS OTP"),
            ap.get("Eligibility Note", "Eligible")
        ))

    # Ensure all 7 auth profiles are present
    for ap in auth_data.get("Authentication Profiles", []):
        acct_no = ap.get("Account No")
        cur.execute("SELECT count(*) FROM accounts WHERE account_no = ?", (acct_no,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
            INSERT INTO accounts (
                account_no, auth_profile_id, investor_name, account_name,
                account_status, registered_email, registered_phone, phone_verified,
                allowed_otp_route, eligibility_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acct_no,
                ap.get("Auth Profile ID"),
                ap.get("Investor Name"),
                ap.get("Investor Name"),
                ap.get("Account Status", "Active"),
                ap.get("Registered Email"),
                ap.get("Registered Phone"),
                ap.get("Phone Verified", "Yes"),
                ap.get("Allowed OTP Route"),
                ap.get("Eligibility Note")
            ))

    # Seed ZILO Trades (19 trades)
    trades = base_data.get("ZILO TRADES", [])
    for t in trades:
        cur.execute("""
        INSERT OR REPLACE INTO trades (
            trade_ref, account_no, fund_name, fund_code, trade_type,
            gross_amount, currency, trade_status, trade_date, settlement_date, scenario
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t.get("Trade Ref"),
            t.get("Account No"),
            t.get("Fund & Class Code") or t.get("Fund Code") or "Global Growth Class A",
            t.get("Fund Code"),
            t.get("Trade Type", "Subscription"),
            float(t.get("Amount", 0) or 0),
            t.get("Currency", "USD"),
            t.get("Status", "Processed"),
            t.get("Trade Date"),
            t.get("Settlement Date"),
            t.get("Scenario")
        ))

    # Seed ZILO Work Items (12 work items)
    work_items = base_data.get("ZILO Work Items", [])
    for idx, w in enumerate(work_items):
        wi_id = w.get("Work Item ID") or f"WI-30{idx+1:02d}"
        cur.execute("""
        INSERT OR REPLACE INTO work_items (
            work_item_id, trade_ref, account_no, queue_name, sub_queue,
            work_item_status, nigo_reason, action_needed, sla, message, scenario
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wi_id,
            w.get("Trade Ref"),
            w.get("Account No"),
            w.get("Queue") or w.get("Current Queue") or "DEALING",
            w.get("Sub-Queue", ""),
            w.get("Sub-Queue") or w.get("Work Item Status") or w.get("Status", "DINDEX"),
            w.get("NIGO Reason / Hold Description") or ("Signature Discrepancy" if "signature" in str(w.get("Comments", "")).lower() else ""),
            w.get("Comments", ""),
            "Same Day 17:00 ET" if "DINDEX" in str(w.get("Sub-Queue", "")) else "Standard SLA",
            w.get("Comments", ""),
            w.get("Scenario")
        ))

    # Seed Bank Reconciliation (6 records)
    bank_rec = base_data.get("Bank Reconciliation", [])
    for b in bank_rec:
        cur.execute("""
        INSERT OR REPLACE INTO bank_rec (
            trade_ref, account_no, bank_rec_status, zilo_status,
            amount, currency, subnr_flag, settlement_date, scenario
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b.get("Trade Ref"),
            b.get("Account No", "ACC-1001"),
            b.get("Bank Rec Status", "Matched"),
            "Settled" if b.get("Bank Rec Status") == "Matched" else "Unsettled",
            float(b.get("Amount Matched") or b.get("Amount") or (2000000.0 if b.get("Trade Ref") == "TRD-5010" else 750000.0 if b.get("Trade Ref") == "TRD-5011" else 1250000.0)),
            b.get("Currency", "USD"),
            b.get("SUBNR Flag", "No"),
            b.get("Settlement Date", "2026-09-18"),
            b.get("Scenario")
        ))

    conn.commit()
    print("Database seeded successfully with all tables.")

if __name__ == "__main__":
    init_db(force_reseed=True)
