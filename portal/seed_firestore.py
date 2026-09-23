#!/usr/bin/env python3
"""Seed Firestore database 'statestreet' with all mock data from State Street spreadsheets."""

import json
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

PROJECT_ID = "gcex-contact-center-508117"
DATABASE_ID = "statestreet"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DATABASE_ID}/documents"

AUTH_DATA_PATH = Path("/usr/local/google/home/stilwalli/mywork/statestreet_research/auth_mock_data.json")
MOCK_DATA_PATH = Path("/usr/local/google/home/stilwalli/mywork/statestreet_research/statestreet_mock_data.json")

def get_access_token():
    token = subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True
    ).strip()
    return token

def to_firestore_value(v):
    if v is None:
        return {"nullValue": None}
    elif isinstance(v, bool):
        return {"booleanValue": v}
    elif isinstance(v, (int, float)):
        return {"doubleValue": float(v)}
    elif isinstance(v, list):
        return {"arrayValue": {"values": [to_firestore_value(item) for item in v]}}
    elif isinstance(v, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(val) for k, val in v.items()}}}
    else:
        return {"stringValue": str(v)}

def firestore_upsert(token, collection, doc_id, data):
    url = f"{BASE_URL}/{collection}/{doc_id}"
    fields = {k: to_firestore_value(v) for k, v in data.items()}
    body = json.dumps({"fields": fields}).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error writing {collection}/{doc_id}: {e.code} - {e.read().decode('utf-8')}")
        raise

def seed_all():
    token = get_access_token()
    print("Starting Firestore seeding for database 'statestreet'...")

    with open(AUTH_DATA_PATH) as f:
        auth_data = json.load(f)

    with open(MOCK_DATA_PATH) as f:
        mock_data = json.load(f)

    auth_profiles = {p.get("Account No"): p for p in auth_data.get("Authentication Profiles", [])}

    # 1. Accounts Collection (28 accounts + auth profile fields)
    print("Seeding accounts...")
    accounts = mock_data.get("Accounts", [])
    for acc in accounts:
        acct_no = acc.get("Account No")
        ap = auth_profiles.get(acct_no, {})
        data = {
            "account_no": acct_no,
            "auth_profile_id": ap.get("Auth Profile ID", f"AUTH-{acct_no[-4:]}"),
            "investor_name": ap.get("Investor Name") or acc.get("Investor Name"),
            "account_name": acc.get("Account Name"),
            "account_status": ap.get("Account Status") or acc.get("Status", "Active"),
            "registered_email": ap.get("Registered Email") or acc.get("Investor Email"),
            "registered_phone": ap.get("Registered Phone", "+1-617-555-0100"),
            "phone_verified": ap.get("Phone Verified", "Yes"),
            "allowed_otp_route": ap.get("Allowed OTP Route", "Email OTP; SMS OTP"),
            "eligibility_note": ap.get("Eligibility Note", "Eligible")
        }
        firestore_upsert(token, "accounts", acct_no, data)
    print(f"  Loaded {len(accounts)} accounts into Firestore.")

    # 2. Trades Collection (19 trades)
    print("Seeding trades...")
    trades = mock_data.get("ZILO TRADES", [])
    for t in trades:
        ref = t.get("Trade Ref")
        data = {
            "trade_ref": ref,
            "account_no": t.get("Account No"),
            "fund_name": t.get("Fund & Class Code") or t.get("Fund Code") or "Global Growth Class A",
            "fund_code": t.get("Fund Code", "GGF-A"),
            "trade_type": t.get("Trade Type", "Subscription"),
            "gross_amount": float(t.get("Amount", 0) or 0),
            "currency": t.get("Currency", "USD"),
            "trade_status": t.get("Status", "Processed"),
            "trade_date": t.get("Trade Date", "2024-09-02"),
            "settlement_date": t.get("Settlement Date", "2024-09-05"),
            "scenario": t.get("Scenario", "")
        }
        firestore_upsert(token, "trades", ref, data)
    print(f"  Loaded {len(trades)} trades into Firestore.")

    # 3. Work Items Collection (12 work items)
    print("Seeding work items...")
    work_items = mock_data.get("ZILO Work Items", [])
    for idx, w in enumerate(work_items):
        wi_id = w.get("Work Item ID") or f"WI-30{idx+1:02d}"
        data = {
            "work_item_id": wi_id,
            "trade_ref": w.get("Trade Ref", ""),
            "account_no": w.get("Account No", ""),
            "queue_name": w.get("Queue") or w.get("Current Queue") or "DEALING",
            "sub_queue": w.get("Sub-Queue", ""),
            "work_item_status": w.get("Sub-Queue") or w.get("Work Item Status") or w.get("Status", "DINDEX"),
            "nigo_reason": w.get("NIGO Reason / Hold Description") or ("Signature Discrepancy" if "signature" in str(w.get("Comments", "")).lower() else ""),
            "action_needed": w.get("Comments", ""),
            "sla": "Same Day 17:00 ET" if "DINDEX" in str(w.get("Sub-Queue", "")) else "Standard SLA",
            "message": w.get("Comments", ""),
            "scenario": w.get("Scenario", "")
        }
        firestore_upsert(token, "work_items", wi_id, data)
    print(f"  Loaded {len(work_items)} work items into Firestore.")

    # 4. Bank Reconciliation Collection (6 records)
    print("Seeding bank reconciliation...")
    bank_rec = mock_data.get("Bank Reconciliation", [])
    for b in bank_rec:
        ref = b.get("Trade Ref")
        amt = float(b.get("Amount Matched") or b.get("Amount") or (2000000.0 if ref == "TRD-5010" else 750000.0 if ref == "TRD-5011" else 1250000.0))
        data = {
            "trade_ref": ref,
            "account_no": b.get("Account No", "ACC-1001"),
            "bank_rec_status": b.get("Bank Rec Status", "Matched"),
            "zilo_status": "Settled" if b.get("Bank Rec Status") == "Matched" else "Unsettled",
            "amount": amt,
            "currency": b.get("Currency", "USD"),
            "subnr_flag": b.get("SUBNR Flag", "No"),
            "settlement_date": b.get("Settlement Date", "2026-09-18"),
            "scenario": b.get("Scenario", "")
        }
        firestore_upsert(token, "bank_rec", ref, data)
    print(f"  Loaded {len(bank_rec)} bank rec records into Firestore.")
    print("Firestore database 'statestreet' seeding complete!")

if __name__ == "__main__":
    seed_all()
