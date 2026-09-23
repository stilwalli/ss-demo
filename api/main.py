from datetime import datetime, timezone
import os
import json
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Path as FastPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google.cloud import firestore
import google.auth
import google.auth.transport.requests
import requests

PROJECT_ID = os.environ.get("PROJECT_ID", "gcex-contact-center-508117")
DATABASE_ID = os.environ.get("DATABASE_ID", "statestreet")
CES_APP_PATH = os.environ.get(
    "CES_APP_PATH",
    "projects/gcex-contact-center-508117/locations/us/apps/954f9664-9865-4fdc-9ced-751589097442"
)
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="State Street Transfer Agency Operations & AI Platform",
    description="Live operational REST API powered by Firestore for GECX/CES Conversational Agent Tara and the State Street Operations Portal.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db = None
def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)
    return _db


# =====================================================================
# Pydantic Models & Schemas for OpenAPI Tools & Portal
# =====================================================================

class AccountResponse(BaseModel):
    status: str = "found"
    account_no: str
    account_name: Optional[str] = None
    investor_name: Optional[str] = None
    registered_email: Optional[str] = None
    registered_phone: Optional[str] = None
    phone_verified: Optional[str] = "No"
    account_status: Optional[str] = "Active"
    auth_profile_id: Optional[str] = None
    allowed_otp_route: Optional[str] = None
    eligibility_note: Optional[str] = None
    agent_action: Optional[str] = None

class OtpIssueRequest(BaseModel):
    account_no: str
    channel: str = Field(default="chat", description="'chat' (email) or 'voice' (sms)")
    target_contact: Optional[str] = None

class OtpIssueResponse(BaseModel):
    status: str
    account_no: str
    channel: str
    target_contact_masked: str
    otp_length: int = 6
    validity_minutes: int = 5
    message: str
    agent_action: str

class OtpValidateRequest(BaseModel):
    account_no: str
    entered_code: str

class OtpValidateResponse(BaseModel):
    status: str
    account_no: str
    authenticated: bool
    message: str
    agent_action: str

class TradeResponse(BaseModel):
    status: str
    trade_ref: Optional[str] = None
    trade_status: Optional[str] = None
    fund_name: Optional[str] = None
    transaction_type: Optional[str] = None
    gross_amount: Optional[float] = None
    trade_date: Optional[str] = None
    nav_date: Optional[str] = None
    settlement_date: Optional[str] = None
    currency: Optional[str] = "USD"
    message: Optional[str] = None
    agent_action: Optional[str] = None

class WorkItemResponse(BaseModel):
    status: str
    trade_ref: Optional[str] = None
    work_item_id: Optional[str] = None
    work_item_status: Optional[str] = None
    queue_name: Optional[str] = None
    sla: Optional[str] = None
    nigo_reason: Optional[str] = None
    action_needed: Optional[str] = None
    message: Optional[str] = None
    agent_action: Optional[str] = None

class BankRecResponse(BaseModel):
    status: str
    trade_ref: Optional[str] = None
    bank_rec_status: Optional[str] = None
    subnr: Optional[str] = None
    cash_received_amount: Optional[float] = None
    rec_date: Optional[str] = None
    settlement_date: Optional[str] = None
    sd_plus_days: Optional[int] = 0
    message: Optional[str] = None
    agent_action: Optional[str] = None

class SettlementInquiryResponse(BaseModel):
    status: str
    trade_ref: str
    zilo_status: Optional[str] = None
    bank_rec_status: Optional[str] = None
    subnr: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    message: str
    agent_action: str

class DiscoveryCandidate(BaseModel):
    masked_trade_ref: str
    transaction_type: str
    fund_name: str
    trade_date: Optional[str] = None
    masked_amount: Optional[str] = None

class DiscoveryResponse(BaseModel):
    status: str
    count: int = 0
    candidates: List[DiscoveryCandidate] = []
    message: Optional[str] = None
    agent_action: str

class TransactionSummaryItem(BaseModel):
    reference: str
    source_system: str
    transaction_type: str
    fund_name: str
    event_date: str
    amount: float
    currency: str = "USD"
    status: str
    sub_queue_or_cash_rec: Optional[str] = None
    action_needed: Optional[str] = None

class TransactionSummaryTotals(BaseModel):
    currency: str
    count: int
    total_amount: float
    processed_count: int = 0
    intake_count: int = 0
    settled_matched_count: int = 0
    pending_settlement_count: int = 0
    overdue_count: int = 0

class TransactionSummaryResponse(BaseModel):
    status: str
    account_no: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    total_records: int
    currencies: List[TransactionSummaryTotals] = []
    transactions: List[TransactionSummaryItem] = []
    voice_summary: str
    agent_action: str
    message: Optional[str] = None

class EscalateRequest(BaseModel):
    account_no: str
    target_queue: str
    reason: str
    context_summary: Optional[str] = ""

class EscalateResponse(BaseModel):
    status: str
    account_no: str
    target_queue: str
    reason: str
    transfer_mode: str = "WARM_TRANSFER"
    message: str
    agent_action: str

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent: Optional[str] = None
    transfer: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = []
    tool_responses: List[Dict[str, Any]] = []
    handoff_dossier: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None


# =====================================================================
# System Health
# =====================================================================

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "project": PROJECT_ID,
        "database": DATABASE_ID,
        "ces_app": CES_APP_PATH
    }


# =====================================================================
# CES Agent OpenAPI Tool Endpoints (CUJ 1, 2, 3)
# =====================================================================

@app.get("/api/v1/accounts/{account_no}", response_model=AccountResponse, tags=["Authentication & Profile"])
def get_account_profile(
    account_no: str = FastPath(..., description="Unique investor account number (e.g. ACC-1001)")
):
    """Retrieves account details and investor profile from the ZILO client master (Firestore: accounts)."""
    acct = account_no.strip().upper()
    db = get_db()
    doc = db.collection("accounts").document(acct).get()

    if not doc.exists:
        return AccountResponse(
            status="not_found",
            account_no=acct,
            agent_action="Verify account number with caller. Prompt caller to re-check or escalate to Identity Verification."
        )

    data = doc.to_dict()
    status = data.get("account_status", "Active")
    phone_verified = data.get("phone_verified", "No")

    agent_action = (
        "Account is inactive. Escalate to Identity Verification immediately."
        if status.lower() == "inactive"
        else "If on voice channel and phone_verified is No, route to Identity Verification. Otherwise proceed with OTP challenge using issue_otp_challenge."
    )

    return AccountResponse(
        status="found",
        account_no=acct,
        account_name=data.get("account_name"),
        investor_name=data.get("investor_name"),
        registered_email=data.get("registered_email"),
        registered_phone=data.get("registered_phone"),
        phone_verified=phone_verified,
        account_status=status,
        auth_profile_id=data.get("auth_profile_id"),
        allowed_otp_route=data.get("allowed_otp_route"),
        eligibility_note=data.get("eligibility_note"),
        agent_action=agent_action
    )


@app.post("/api/v1/accounts/otp/issue", response_model=OtpIssueResponse, tags=["Authentication & Profile"])
def issue_otp(request: OtpIssueRequest):
    """Issues a 6-digit MFA OTP challenge via Email or SMS."""
    acct = request.account_no.strip().upper()
    channel = request.channel.lower()
    
    db = get_db()
    doc = db.collection("accounts").document(acct).get()
    contact = request.target_contact
    if doc.exists:
        data = doc.to_dict()
        if not contact:
            contact = data.get("registered_email") if channel == "chat" else data.get("registered_phone")

    if not contact:
        contact = "s.***@apexglobal.com" if channel == "chat" else "+1-***-***-0142"

    return OtpIssueResponse(
        status="challenge_issued",
        account_no=acct,
        channel=channel,
        target_contact_masked=contact,
        otp_length=6,
        validity_minutes=5,
        message=f"A 6-digit verification code has been sent to {contact}.",
        agent_action="Prompt the user to provide the 6-digit verification code received."
    )


@app.post("/api/v1/accounts/otp/validate", response_model=OtpValidateResponse, tags=["Authentication & Profile"])
def validate_otp(request: OtpValidateRequest):
    """Validates the user-entered 6-digit MFA OTP code."""
    acct = request.account_no.strip().upper()
    code = request.entered_code.strip()

    if code in ["123456", "847291", "482910"]:
        return OtpValidateResponse(
            status="authenticated",
            account_no=acct,
            authenticated=True,
            message="Authentication successful.",
            agent_action="Silently route to requested specialist agent (Deal_Tickets_Agent or Receipt_of_Monies_Agent)."
        )
    else:
        return OtpValidateResponse(
            status="failed",
            account_no=acct,
            authenticated=False,
            message="Invalid verification code entered.",
            agent_action="Prompt user to re-enter code. If 3 attempts fail, route to Identity Verification."
        )


@app.get("/api/v1/trades/discovery", response_model=DiscoveryResponse, tags=["Deal Tickets"])
def agentic_discovery_deal_ticket(
    account_no: str = Query(..., description="Authenticated investor account number"),
    txn_type: Optional[str] = Query(None, description="Transaction type: Subscription or Redemption"),
    fund_code: Optional[str] = Query(None, description="Fund identifier or name keyword"),
    date_str: Optional[str] = Query(None, description="Trade or order date (YYYY-MM-DD)"),
    amount_str: Optional[str] = Query(None, description="Approximate dollar amount")
):
    """Searches for trades by non-monetary clues with 2-clue privacy gate."""
    clues = []
    if txn_type: clues.append("txn_type")
    if fund_code: clues.append("fund_code")
    if date_str: clues.append("date_str")

    if amount_str and len(clues) == 0:
        return DiscoveryResponse(
            status="privacy_gate_rejected",
            count=0,
            message="Amount alone is insufficient to search transactions under privacy regulations.",
            agent_action="Prompt caller for transaction type, date, or fund name."
        )

    if len(clues) < 2:
        return DiscoveryResponse(
            status="insufficient_clues",
            count=0,
            message="At least two corroborating clues are required for deal discovery.",
            agent_action="Request additional details such as transaction date or fund name."
        )

    return DiscoveryResponse(
        status="candidates_found",
        count=1,
        candidates=[
            DiscoveryCandidate(
                masked_trade_ref="***5102",
                transaction_type=txn_type or "Subscription",
                fund_name="Global Growth Class A",
                trade_date=date_str or "2026-09-18",
                masked_amount="$500,***"
            )
        ],
        agent_action="Confirm candidate match with caller before disclosing full details."
    )


@app.get("/api/v1/trades/{trade_ref}", response_model=TradeResponse, tags=["Deal Tickets"])
def get_trade_status(
    trade_ref: str = FastPath(..., description="Unique trade reference (e.g. TRD-5001)"),
    account_no: Optional[str] = Query(None, description="Authenticated investor account number for isolation check")
):
    """Searches ZILO Works for deterministic trade execution status."""
    ref = trade_ref.strip().upper()
    db = get_db()
    doc = db.collection("trades").document(ref).get()

    if not doc.exists:
        return TradeResponse(
            status="not_in_zilo_works",
            trade_ref=ref,
            message=f"Trade {ref} not found in ZILO Works.",
            agent_action="Check ZILO Work Items using search_work_item. If also not found there, ask caller to verify the trade reference number or offer to search by date and fund name."
        )

    t = doc.to_dict()
    accounts = t.get("account_no", [])
    if isinstance(accounts, str):
        accounts = [accounts]

    if account_no:
        acct_clean = account_no.strip().upper()
        if acct_clean not in accounts:
            return TradeResponse(
                status="unauthorized",
                trade_ref=ref,
                message=f"Trade {ref} does not belong to authenticated account {acct_clean}.",
                agent_action="Inform caller that the trade reference does not belong to their authenticated account. Proactively ask if they would like to verify the trade reference number, or ask what other trade or transaction you can assist them with today."
            )

    return TradeResponse(
        status="found",
        trade_ref=ref,
        trade_status=t.get("trade_status") or t.get("status"),
        fund_name=t.get("fund_name") or t.get("fund"),
        transaction_type=t.get("trade_type") or t.get("type") or t.get("transaction_type"),
        gross_amount=float(t.get("gross_amount") or t.get("amount") or 0.0),
        trade_date=t.get("trade_date"),
        nav_date=t.get("nav_date"),
        settlement_date=t.get("settlement_date"),
        currency=t.get("currency", "USD"),
        agent_action="Report factual trade details to caller."
    )


@app.get("/api/v1/work-items/{reference}", response_model=WorkItemResponse, tags=["Deal Tickets"])
def get_work_item(
    reference: str = FastPath(..., description="Unique work item ID (WI-3001) or Trade Ref (TRD-5003, TRD-5004)"),
    account_no: Optional[str] = Query(None, description="Authenticated investor account number")
):
    """Searches ZILO Work Items by Work Item ID or Trade Reference for document indexing (DINDEX) or NIGO exceptions."""
    ref = reference.strip().upper()
    db = get_db()

    doc = db.collection("work_items").document(ref).get()
    w = None
    if doc.exists:
        w = doc.to_dict()
    else:
        q = db.collection("work_items").where("trade_ref", "==", ref).limit(1).stream()
        matches = list(q)
        if matches:
            w = matches[0].to_dict()

    if not w:
        return WorkItemResponse(
            status="not_found",
            trade_ref=ref,
            message=f"Work item for {ref} not found in ZILO Work Items.",
            agent_action="Advise caller that trade reference could not be located in processing or intake queues. Proactively ask if they would like to verify the trade reference number, or ask what other trade or inquiry you can assist them with today."
        )

    accounts = w.get("account_no", [])
    if isinstance(accounts, str):
        accounts = [accounts]

    if account_no:
        acct_clean = account_no.strip().upper()
        if acct_clean not in accounts:
            return WorkItemResponse(
                status="unauthorized",
                trade_ref=ref,
                message=f"Work item {ref} does not belong to authenticated account {acct_clean}.",
                agent_action="Inform caller that the work item reference does not belong to their authenticated account. Proactively ask if they would like to verify the reference number, or ask what other trade or transaction you can assist them with today."
            )

    status = w.get("work_item_status") or w.get("status", "DINDEX")
    trade_ref = w.get("trade_ref", ref)
    work_id = w.get("work_item_id", ref)

    if status == "DINDEX":
        return WorkItemResponse(
            status="found",
            trade_ref=trade_ref,
            work_item_id=work_id,
            work_item_status="DINDEX",
            queue_name=w.get("queue_name") or w.get("queue", "Document Indexing"),
            sla=w.get("sla", "Same Day 17:00 ET"),
            message=w.get("message", "Trade document is currently in Document Indexing queue for intake."),
            agent_action=f"Inform caller document is indexing with SLA of {w.get('sla', 'Same Day 17:00 ET')}."
        )
    elif status in ["NIGO", "REJECTED"]:
        return WorkItemResponse(
            status="found",
            trade_ref=trade_ref,
            work_item_id=work_id,
            work_item_status=status,
            queue_name=w.get("queue_name") or w.get("queue", "Exception Review"),
            nigo_reason=w.get("nigo_reason", "Signature Discrepancy"),
            action_needed=w.get("action_needed", "Signatory verification required"),
            message=w.get("message", "Trade is flagged Not In Good Order."),
            agent_action="Route to Investor Services (Human) using escalate_interaction."
        )
    else:
        return WorkItemResponse(
            status="found",
            trade_ref=trade_ref,
            work_item_id=work_id,
            work_item_status=status,
            queue_name=w.get("queue_name") or w.get("queue", "General"),
            message=w.get("message", "Work item in progress."),
            agent_action="Report queue status to caller."
        )


@app.get("/api/v1/bank-rec/{trade_ref}", response_model=BankRecResponse, tags=["Receipt of Monies"])
def get_bank_rec(
    trade_ref: str = FastPath(..., description="Unique trade reference (e.g. TRD-5010, TRD-5012)"),
    account_no: Optional[str] = Query(None, description="Authenticated investor account number")
):
    """Queries Bank Reconciliation system for cash receipt match status."""
    ref = trade_ref.strip().upper()
    db = get_db()
    doc = db.collection("bank_rec").document(ref).get()

    if not doc.exists:
        return BankRecResponse(
            status="not_found",
            trade_ref=ref,
            message=f"No bank rec record found for {ref}.",
            agent_action="Confirm trade settlement date or escalate to Cash Management."
        )

    r = doc.to_dict()
    subnr = r.get("subnr_flag") or r.get("subnr", "No")
    return BankRecResponse(
        status="found",
        trade_ref=ref,
        bank_rec_status=r.get("bank_rec_status", "Unmatched"),
        subnr=subnr,
        cash_received_amount=float(r.get("amount") or r.get("cash_received") or 0.0),
        rec_date=r.get("rec_date"),
        settlement_date=r.get("settlement_date"),
        sd_plus_days=int(r.get("sd_plus_days") or 0),
        agent_action="If Matched report monies received; if Unmatched and SUBNR:Yes escalate to Cash Management."
    )


@app.get("/api/v1/settlement/inquiry/{trade_ref}", response_model=SettlementInquiryResponse, tags=["Receipt of Monies"])
def execute_settlement_inquiry(
    trade_ref: str = FastPath(..., description="Unique trade reference"),
    account_no: Optional[str] = Query(None, description="Authenticated investor account number")
):
    """Comprehensive settlement evaluation across ZILO Trades, Bank Rec, and SUBNR."""
    ref = trade_ref.strip().upper()
    db = get_db()

    trade_doc = db.collection("trades").document(ref).get()
    bank_doc = db.collection("bank_rec").document(ref).get()

    if not trade_doc.exists:
        return SettlementInquiryResponse(
            status="not_found",
            trade_ref=ref,
            message=f"Trade {ref} not found for settlement evaluation.",
            agent_action="Advise caller that trade reference could not be located. Proactively ask if they would like to verify the reference number, or ask what other trade or settlement inquiry you can assist them with today."
        )

    t = trade_doc.to_dict()
    accounts = t.get("account_no", [])
    if isinstance(accounts, str): accounts = [accounts]

    if account_no and account_no.strip().upper() not in accounts:
        return SettlementInquiryResponse(
            status="unauthorized",
            trade_ref=ref,
            message=f"Trade {ref} does not belong to authenticated account {account_no}.",
            agent_action="Inform caller that the trade reference does not belong to their authenticated account. Proactively ask if they would like to verify the trade reference number, or ask what other trade or settlement inquiry you can assist them with today."
        )

    trade_status = t.get("trade_status") or t.get("status", "Unsettled")
    amount = float(t.get("gross_amount") or t.get("amount") or 0.0)

    bank_rec_status = "Unmatched"
    subnr = "No"
    if bank_doc.exists:
        b = bank_doc.to_dict()
        bank_rec_status = b.get("bank_rec_status", "Unmatched")
        subnr = b.get("subnr_flag") or b.get("subnr", "No")

    if trade_status == "Settled" and bank_rec_status == "Matched":
        return SettlementInquiryResponse(
            status="settled_and_matched",
            trade_ref=ref,
            zilo_status="Settled",
            bank_rec_status="Matched",
            subnr="No",
            amount=amount,
            message=f"Monies received and matched in full (${amount:,.2f}). Trade settled.",
            agent_action=f"Inform caller that full settlement monies of ${amount:,.2f} are received and posted."
        )
    elif subnr.lower() in ["yes", "y", "true"]:
        return SettlementInquiryResponse(
            status="overdue_subnr_escalation",
            trade_ref=ref,
            zilo_status="Unsettled",
            bank_rec_status="Unmatched",
            subnr="Yes",
            amount=amount,
            message=f"Monies overdue at Settlement Date + 1 with SUBNR flag active (${amount:,.2f}).",
            agent_action="Immediately escalate to Cash Management queue via escalate_interaction."
        )
    else:
        return SettlementInquiryResponse(
            status="unsettled_in_cycle",
            trade_ref=ref,
            zilo_status="Unsettled",
            bank_rec_status=bank_rec_status,
            subnr="No",
            amount=amount,
            message="Trade is currently within normal settlement window (SD).",
            agent_action="Inform caller that settlement is in-cycle and monitoring will continue."
        )


def _parse_flex_date(val: Any) -> Optional[datetime]:
    if not val or not isinstance(val, str) or val.strip() in ["", "N/A", "null"]:
        return None
    val_clean = val.strip()
    # Try DD/MM/YYYY
    try:
        return datetime.strptime(val_clean[:10], "%d/%m/%Y")
    except ValueError:
        pass
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(val_clean[:10], "%Y-%m-%d")
    except ValueError:
        pass
    return None


@app.get("/api/v1/accounts/{account_no}/transactions-summary", response_model=TransactionSummaryResponse, tags=["Deal Tickets"])
def get_transactions_summary(
    account_no: str = FastPath(..., description="Unique investor account number (e.g. ACC-1001)"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD or DD/MM/YYYY)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD or DD/MM/YYYY)")
):
    """Retrieves an aggregated, deduplicated transaction summary across ZILO Trades, Work Items, and Bank Rec.
    
    Implements Tab 4 (Transaction Summary) and Tab 5 (Date Range Summary) from the State Street CUJ workbook.
    """
    acct = account_no.strip().upper()
    db = get_db()

    # Normalize Query default parameter if called as a standard function in Python
    d_from = str(date_from).strip() if (date_from and isinstance(date_from, str)) else None
    d_to = str(date_to).strip() if (date_to and isinstance(date_to, str)) else None

    # 1. Date Range Validation (Tab 5 Step 2)
    parsed_from = _parse_flex_date(d_from) if d_from else None
    parsed_to = _parse_flex_date(d_to) if d_to else None

    if d_from and not parsed_from:
        return TransactionSummaryResponse(
            status="invalid_date_format",
            account_no=acct,
            total_records=0,
            voice_summary=f"The start date '{d_from}' is in an unrecognized format. Please use YYYY-MM-DD.",
            agent_action="Prompt caller for valid start date format.",
            message="Invalid date_from format."
        )

    if d_to and not parsed_to:
        return TransactionSummaryResponse(
            status="invalid_date_format",
            account_no=acct,
            total_records=0,
            voice_summary=f"The end date '{d_to}' is in an unrecognized format. Please use YYYY-MM-DD.",
            agent_action="Prompt caller for valid end date format.",
            message="Invalid date_to format."
        )

    if parsed_from and parsed_to and parsed_from > parsed_to:
        return TransactionSummaryResponse(
            status="invalid_date_range",
            account_no=acct,
            date_from=date_from,
            date_to=date_to,
            total_records=0,
            voice_summary="The start date you provided is after the end date. Could you please confirm the date range?",
            agent_action="Advise caller of inverted date range and prompt for correct start and end dates.",
            message="Start date cannot be after end date."
        )

    # 2. Query ZILO Trades for Account
    trades_docs = db.collection("trades").stream()
    matched_trades = []
    trade_refs_seen = set()

    for doc in trades_docs:
        d = doc.to_dict()
        accounts = d.get("account_no", [])
        if isinstance(accounts, str): accounts = [accounts]
        if acct not in accounts:
            continue

        trade_ref = d.get("trade_ref") or doc.id
        trade_date_str = d.get("trade_date") or ""
        trade_date_obj = _parse_flex_date(trade_date_str)

        # Date Filtering on Trade Date (Tab 5 Step 5)
        if parsed_from and trade_date_obj and trade_date_obj < parsed_from:
            continue
        if parsed_to and trade_date_obj and trade_date_obj > parsed_to:
            continue

        trade_refs_seen.add(trade_ref)
        matched_trades.append((trade_ref, d, trade_date_obj, trade_date_str))

    # 3. Query ZILO Work Items for Account with Deduplication (Tab 4 & 5 Steps 6-7)
    wi_docs = db.collection("work_items").stream()
    matched_work_items = []

    for doc in wi_docs:
        w = doc.to_dict()
        accounts = w.get("account_no", [])
        if isinstance(accounts, str): accounts = [accounts]
        if acct not in accounts:
            continue

        ref = w.get("trade_ref") or doc.id
        # Deduplication Rule: If already in ZILO Trades, drop the raw work item
        if ref in trade_refs_seen:
            continue

        create_date_str = w.get("create_date") or w.get("created_at") or ""
        create_date_obj = _parse_flex_date(create_date_str)

        # Date Filtering on Create Date/Time (Tab 5 Step 6)
        if parsed_from and create_date_obj and create_date_obj < parsed_from:
            continue
        if parsed_to and create_date_obj and create_date_obj > parsed_to:
            continue

        matched_work_items.append((ref, w, create_date_obj, create_date_str))

    # 4. Synthesize Items & Link Bank Rec (Tab 4 & 5 Step 10)
    items: List[TransactionSummaryItem] = []

    for trade_ref, d, dt_obj, dt_str in matched_trades:
        status = d.get("trade_status") or d.get("status", "Processed")
        amount = float(d.get("gross_amount") or d.get("amount") or 0.0)
        curr = d.get("currency") or "USD"
        fund = d.get("fund_name") or d.get("fund") or d.get("fund_code") or "General Fund"
        ttype = d.get("transaction_type") or d.get("trade_type") or "Subscription"

        sub_info = None
        action = "None"

        # Check Bank Rec for Settled / Unsettled trades
        if status in ["Settled", "Unsettled"]:
            b_doc = db.collection("bank_rec").document(trade_ref).get()
            if b_doc.exists:
                b = b_doc.to_dict()
                b_status = b.get("bank_rec_status", "Unmatched")
                subnr = b.get("subnr_flag") or b.get("subnr", "No")
                if b_status == "Matched":
                    sub_info = "Cash Matched"
                    action = "None"
                elif subnr.lower() in ["yes", "y", "true"]:
                    sub_info = "Overdue (SUBNR Active)"
                    action = "Escalate to Cash Management"
                else:
                    sub_info = "Cash In-Cycle (Monitoring)"
                    action = "Monitoring"

        items.append(TransactionSummaryItem(
            reference=trade_ref,
            source_system="ZILO Works",
            transaction_type=ttype,
            fund_name=fund,
            event_date=dt_str or "N/A",
            amount=amount,
            currency=curr,
            status=status,
            sub_queue_or_cash_rec=sub_info,
            action_needed=action
        ))

    for ref, w, c_obj, c_str in matched_work_items:
        queue = w.get("queue") or "DEALING"
        sub_queue = w.get("sub_queue") or w.get("work_item_status") or "DINDEX"
        amount = float(w.get("amount") or 0.0)
        curr = w.get("currency") or "USD"
        fund = w.get("fund_name") or w.get("fund") or "Fund"
        ttype = w.get("trade_type") or w.get("work_type") or "Subscription"

        action = "Awaiting intake checks"
        if sub_queue == "NIGO":
            action = "Re-sign documentation (Signature Discrepancy)"

        items.append(TransactionSummaryItem(
            reference=ref,
            source_system="ZILO Work Items",
            transaction_type=ttype,
            fund_name=fund,
            event_date=c_str or "N/A",
            amount=amount,
            currency=curr,
            status=f"Intake Queue ({sub_queue})",
            sub_queue_or_cash_rec=f"Queue: {queue} / {sub_queue}",
            action_needed=action
        ))

    # Sort items by date descending
    items.sort(key=lambda x: x.event_date, reverse=True)

    # 5. Multi-Currency Aggregations (Tab 5 Step 12)
    currencies_dict: Dict[str, Dict[str, Any]] = {}
    for item in items:
        c = item.currency
        if c not in currencies_dict:
            currencies_dict[c] = {
                "count": 0,
                "total_amount": 0.0,
                "processed": 0,
                "intake": 0,
                "matched": 0,
                "pending_settlement": 0,
                "overdue": 0
            }
        currencies_dict[c]["count"] += 1
        currencies_dict[c]["total_amount"] += item.amount

        if "Processed" in item.status:
            currencies_dict[c]["processed"] += 1
        elif "Intake" in item.status:
            currencies_dict[c]["intake"] += 1
        
        if item.sub_queue_or_cash_rec:
            if "Cash Matched" in item.sub_queue_or_cash_rec:
                currencies_dict[c]["matched"] += 1
            elif "Overdue" in item.sub_queue_or_cash_rec:
                currencies_dict[c]["overdue"] += 1
            elif "In-Cycle" in item.sub_queue_or_cash_rec:
                currencies_dict[c]["pending_settlement"] += 1

    totals_list: List[TransactionSummaryTotals] = []
    for c, stats in currencies_dict.items():
        totals_list.append(TransactionSummaryTotals(
            currency=c,
            count=stats["count"],
            total_amount=stats["total_amount"],
            processed_count=stats["processed"],
            intake_count=stats["intake"],
            settled_matched_count=stats["matched"],
            pending_settlement_count=stats["pending_settlement"],
            overdue_count=stats["overdue"]
        ))

    # 6. Pre-computed Voice Summary (Tab 4 Step 14, Tab 5 Step 15)
    if not items:
        voice_summary = "There are no transactions on record for your authenticated account."
        if date_from or date_to:
            voice_summary += f" for the requested date period."
    else:
        parts = []
        for tot in totals_list:
            subparts = []
            if tot.processed_count: subparts.append(f"{tot.processed_count} processed")
            if tot.intake_count: subparts.append(f"{tot.intake_count} in intake review")
            if tot.settled_matched_count: subparts.append(f"{tot.settled_matched_count} settled and cash matched")
            if tot.pending_settlement_count: subparts.append(f"{tot.pending_settlement_count} in-cycle settlement")
            if tot.overdue_count: subparts.append(f"{tot.overdue_count} overdue settlement")
            details_str = ", ".join(subparts) if subparts else f"{tot.count} transactions"
            parts.append(f"{tot.count} in {tot.currency} totaling ${tot.total_amount:,.2f} ({details_str})")
        
        period_str = f"between {d_from} and {d_to}" if (d_from and d_to) else "across your account"
        voice_summary = f"You have a total of {len(items)} transactions {period_str}: {'; '.join(parts)}. Would you like me to provide details on a specific transaction?"

    return TransactionSummaryResponse(
        status="success",
        account_no=acct,
        date_from=d_from,
        date_to=d_to,
        total_records=len(items),
        currencies=totals_list,
        transactions=items,
        voice_summary=voice_summary,
        agent_action="Report pre-computed voice_summary for voice channel, or render transactions table for chat.",
        message=f"Found {len(items)} transactions for account {acct}."
    )


@app.post("/api/v1/escalations", response_model=EscalateResponse, tags=["Escalations"])
def escalate_interaction(request: EscalateRequest):
    """Transfers the interaction to one of the 6 specialized escalation queues."""
    valid_queues = [
        "Identity Verification",
        "Security",
        "Technical Support",
        "Account Management",
        "Cash Management",
        "Investor Services (Human)"
    ]
    q = request.target_queue if request.target_queue in valid_queues else "Investor Services (Human)"
    return EscalateResponse(
        status="escalation_initiated",
        account_no=request.account_no,
        target_queue=q,
        reason=request.reason,
        transfer_mode="WARM_TRANSFER",
        message=f"Interaction routed to {q}.",
        agent_action=f"Provide professional transition statement to caller connecting to {q}."
    )


# =====================================================================
# Portal Operations CRUD API (Powers Portal Data Grid)
# =====================================================================

@app.get("/api/accounts", tags=["Portal Operations"])
def list_accounts():
    db = get_db()
    docs = [d.to_dict() for d in db.collection("accounts").stream()]
    docs.sort(key=lambda x: str(x.get("account_no", "")))
    return docs

@app.post("/api/accounts", tags=["Portal Operations"])
def create_account(data: Dict[str, Any]):
    acct = str(data.get("account_no", "")).strip().upper()
    if not acct:
        raise HTTPException(status_code=400, detail="account_no required")
    db = get_db()
    db.collection("accounts").document(acct).set(data)
    return {"status": "created", "account_no": acct}

@app.put("/api/accounts/{account_no}", tags=["Portal Operations"])
def update_account(account_no: str, data: Dict[str, Any]):
    acct = account_no.strip().upper()
    db = get_db()
    db.collection("accounts").document(acct).set(data, merge=True)
    return {"status": "updated", "id": acct}

@app.get("/api/trades", tags=["Portal Operations"])
def list_trades():
    db = get_db()
    docs = [d.to_dict() for d in db.collection("trades").stream()]
    docs.sort(key=lambda x: str(x.get("trade_ref", "")))
    return docs

@app.post("/api/trades", tags=["Portal Operations"])
def create_trade(data: Dict[str, Any]):
    ref = str(data.get("trade_ref", "")).strip().upper()
    if not ref:
        raise HTTPException(status_code=400, detail="trade_ref required")
    db = get_db()
    db.collection("trades").document(ref).set(data)
    return {"status": "created", "trade_ref": ref}

@app.put("/api/trades/{trade_ref}", tags=["Portal Operations"])
def update_trade(trade_ref: str, data: Dict[str, Any]):
    ref = trade_ref.strip().upper()
    db = get_db()
    db.collection("trades").document(ref).set(data, merge=True)
    return {"status": "updated", "id": ref}

@app.get("/api/work-items", tags=["Portal Operations"])
def list_work_items():
    db = get_db()
    docs = [d.to_dict() for d in db.collection("work_items").stream()]
    docs.sort(key=lambda x: str(x.get("work_item_id", "")))
    return docs

@app.post("/api/work-items", tags=["Portal Operations"])
def create_work_item(data: Dict[str, Any]):
    wid = str(data.get("work_item_id", "")).strip().upper()
    if not wid:
        raise HTTPException(status_code=400, detail="work_item_id required")
    db = get_db()
    db.collection("work_items").document(wid).set(data)
    return {"status": "created", "work_item_id": wid}

@app.put("/api/work-items/{work_item_id}", tags=["Portal Operations"])
def update_work_item(work_item_id: str, data: Dict[str, Any]):
    wid = work_item_id.strip().upper()
    db = get_db()
    db.collection("work_items").document(wid).set(data, merge=True)
    return {"status": "updated", "id": wid}

@app.get("/api/bank-rec", tags=["Portal Operations"])
def list_bank_rec():
    db = get_db()
    docs = [d.to_dict() for d in db.collection("bank_rec").stream()]
    docs.sort(key=lambda x: str(x.get("trade_ref", "")))
    return docs

@app.post("/api/bank-rec", tags=["Portal Operations"])
def create_bank_rec(data: Dict[str, Any]):
    ref = str(data.get("trade_ref", "")).strip().upper()
    if not ref:
        raise HTTPException(status_code=400, detail="trade_ref required")
    db = get_db()
    db.collection("bank_rec").document(ref).set(data)
    return {"status": "created", "trade_ref": ref}

@app.put("/api/bank-rec/{trade_ref}", tags=["Portal Operations"])
def update_bank_rec(trade_ref: str, data: Dict[str, Any]):
    ref = trade_ref.strip().upper()
    db = get_db()
    db.collection("bank_rec").document(ref).set(data, merge=True)
    return {"status": "updated", "id": ref}

@app.get("/api/stats", tags=["Portal Operations"])
def get_stats():
    db = get_db()
    accs = len(list(db.collection("accounts").stream()))
    trades = len(list(db.collection("trades").stream()))
    wis = len(list(db.collection("work_items").stream()))
    brec = len(list(db.collection("bank_rec").stream()))
    return {
        "database": DATABASE_ID,
        "project": PROJECT_ID,
        "accounts_count": accs,
        "trades_count": trades,
        "work_items_count": wis,
        "bank_rec_count": brec
    }

@app.post("/api/reset", tags=["Portal Operations"])
def reset_database():
    """Resets Firestore database 'statestreet' to the authoritative baseline mock data."""
    auth_file = DATA_DIR / "auth_mock_data.json"
    mock_file = DATA_DIR / "statestreet_mock_data.json"

    if not auth_file.exists() or not mock_file.exists():
        raise HTTPException(status_code=500, detail="Baseline mock data files not found in container.")

    with open(auth_file) as f:
        auth_data = json.load(f)
    with open(mock_file) as f:
        mock_data = json.load(f)

    auth_profiles = {p.get("Account No"): p for p in auth_data.get("Authentication Profiles", [])}
    db = get_db()

    # 1. Accounts
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
        db.collection("accounts").document(acct_no).set(data)

    # 2. Trades
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
        db.collection("trades").document(ref).set(data)

    # 3. Work Items
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
        db.collection("work_items").document(wi_id).set(data)

    # 4. Bank Reconciliation
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
        db.collection("bank_rec").document(ref).set(data)

    return {
        "status": "success",
        "message": f"Successfully restored {len(accounts)} accounts, {len(trades)} trades, {len(work_items)} work items, and {len(bank_rec)} bank rec records to Firestore baseline."
    }


# =====================================================================
# Live AI Chat Assistant Endpoint (Proxy to CES Agent Tara)
# =====================================================================

def build_handoff_dossier(agent: str, transfer: Optional[str], tool_calls: List[Dict[str, Any]], reply: str, user_msg: str) -> Optional[Dict[str, Any]]:
    """Synthesizes structured warm-transfer case dossier and notes for Agent Assist screen-pop."""
    is_escalation = False
    queue = None
    reason = None
    account_no = None

    for tc in tool_calls:
        t_name = str(tc.get("tool", "")).lower()
        if "escalat" in t_name:
            is_escalation = True
            args = tc.get("args", {})
            queue = args.get("target_queue")
            reason = args.get("reason")
            account_no = args.get("account_no")
            break

    trans_str = str(transfer or "").lower()
    agent_str = str(agent or "").lower()
    if "escalat" in trans_str or "escalat" in agent_str:
        is_escalation = True

    combined_text = (reply + " " + user_msg).lower()
    if not is_escalation:
        for q in ["cash management", "investor services", "identity verification", "account management", "technical support", "security"]:
            if f"connecting you with {q}" in combined_text or f"transferring you to {q}" in combined_text or f"route to {q}" in combined_text or f"connect you to {q}" in combined_text:
                is_escalation = True
                queue = q.title()
                break

    if not is_escalation:
        return None

    # Resolve Queue
    if not queue:
        if "cash" in combined_text or "subnr" in combined_text or "5012" in combined_text:
            queue = "Cash Management"
        elif "nigo" in combined_text or "signature" in combined_text or "5004" in combined_text or "representative" in combined_text or "human" in combined_text:
            queue = "Investor Services (Human)"
        elif "suspend" in combined_text or "closed" in combined_text or "1005" in combined_text:
            queue = "Account Management"
        elif "otp" in combined_text or "verification code" in combined_text or "identity" in combined_text:
            queue = "Identity Verification"
        else:
            queue = "Investor Services (Human)"

    # Resolve Reason
    if not reason:
        if "5004" in combined_text or "signature" in combined_text:
            reason = "Trade TRD-5004 held in NIGO exception queue due to missing authorized signature"
        elif "5012" in combined_text or "subnr" in combined_text:
            reason = "Settlement monies overdue at SD+1 with active SUBNR exception flag"
        elif "suspend" in combined_text or "1005" in combined_text:
            reason = "Account ACC-1005 profile is in Suspended status"
        elif "otp" in combined_text:
            reason = "Three consecutive multi-factor authentication attempts failed"
        else:
            reason = "Investor requested live human representative assistance"

    # Resolve Account
    if not account_no:
        if "1005" in combined_text: account_no = "ACC-1005"
        elif "1002" in combined_text: account_no = "ACC-1002"
        elif "1003" in combined_text: account_no = "ACC-1003"
        elif "1004" in combined_text: account_no = "ACC-1004"
        else: account_no = "ACC-1001"

    investor_map = {
        "ACC-1001": "Meridian Capital Partners",
        "ACC-1002": "Beacon Hill Asset Management",
        "ACC-1003": "Vanguard Horizon Trust",
        "ACC-1004": "BlackRock Prime Portfolios",
        "ACC-1005": "Apex Global Strategies",
        "ACC-1020": "Highland Park Advisors",
        "ACC-1022": "Sovereign Wealth Trust"
    }
    investor_name = investor_map.get(account_no, "Meridian Capital Partners")

    action_map = {
        "Investor Services (Human)": "Verify caller authority and provide secondary authorized signature submission link for NIGO remediation.",
        "Cash Management": "Perform bank reconciliation trace in SWIFT/Fedwire settlement ledger for pending cash match.",
        "Account Management": "Verify institutional documentation to review suspended account restriction.",
        "Identity Verification": "Conduct out-of-band identity verification challenge with primary compliance officer.",
        "Technical Support": "Investigate downstream database connection latency and retry transaction lookup."
    }
    suggested_action = action_map.get(queue, "Review interaction telemetry and assist caller with immediate resolution.")

    summary_text = (
        f"Caller authenticated under {account_no} ({investor_name}). "
        f"Inquiry escalated to {queue} due to: {reason}. "
        f"Full conversation trace and context preserved for warm transfer."
    )

    return {
        "account_no": account_no,
        "investor_name": investor_name,
        "auth_status": "MFA Verified (Email OTP: ops@meridiancap.example)" if account_no != "ACC-1005" else "Suspended Profile",
        "target_queue": queue,
        "reason": reason,
        "case_summary": summary_text,
        "suggested_action": suggested_action,
        "transfer_mode": "WARM_TRANSFER (Zero-Repetition)",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat Assistant"])
def chat_with_agent(req: ChatRequest):
    """Executes a live conversational turn against the deployed CES Agent 'StateStreetGECXDemo'."""
    sid = req.session_id or f"web-{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    # Get credentials for CES API
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    token = creds.token

    url = f"https://ces.googleapis.com/v1/{CES_APP_PATH}/sessions/{sid}:runSession"
    payload = {
        "inputs": [
            {
                "text": req.message
            }
        ]
    }

    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"CES Error: {resp.text}")
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with CES Session Service: {str(e)}")

    outputs = data.get("outputs", [])
    reply = ""
    agent = "StateStreetGECXDemo"
    transfer = None
    tool_calls = []
    tool_responses = []

    collected_texts = []
    for out in outputs:
        t = (out.get("text") or "").strip()
        if t:
            collected_texts.append(t)
        diag = out.get("diagnosticInfo", {})
        for msg in diag.get("messages", []):
            role = msg.get("role", "")
            if role and role != "user":
                agent = role
            for ch in msg.get("chunks", []):
                if "agentTransfer" in ch:
                    at = ch["agentTransfer"]
                    transfer = at.get("displayName") or at.get("targetAgent", "")
                if "toolCall" in ch:
                    tc = ch["toolCall"]
                    tool_calls.append({
                        "tool": tc.get("displayName") or tc.get("tool"),
                        "args": tc.get("args", {})
                    })
                if "toolResponse" in ch:
                    tr = ch["toolResponse"]
                    tool_responses.append({
                        "tool": tr.get("displayName") or tr.get("tool"),
                        "response": tr.get("response", {})
                    })

    # Consolidate best reply text: filter out generic fallback if informative answer is present
    informative_texts = [t for t in collected_texts if "trouble with that" not in t.lower()]
    if informative_texts:
        reply = " ".join(informative_texts)
    elif collected_texts:
        reply = " ".join(collected_texts)
    else:
        reply = "Your inquiry has been received and processed by State Street systems."

    # Build handoff dossier if escalation occurred
    dossier = build_handoff_dossier(
        agent=agent,
        transfer=transfer,
        tool_calls=tool_calls,
        reply=reply,
        user_msg=req.message
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    return ChatResponse(
        session_id=sid,
        reply=reply,
        agent=agent,
        transfer=transfer,
        tool_calls=tool_calls,
        tool_responses=tool_responses,
        handoff_dossier=dossier,
        latency_ms=elapsed_ms
    )


# =====================================================================
# Mount Static Frontend (Portal UI)
# =====================================================================
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
