# State Street Transfer Agency AI Assistant — Comprehensive QA Test Scenarios

This test suite provides **5 turn-by-turn conversational test scenarios** designed specifically for QA specialists, developers, and testers evaluating the **Google Customer Engagement Suite (CES)** and **CX Agent Studio (CXAS)** multi-agent architecture for State Street Transfer Agency.

---

### System Architecture Summary & Agent Delegation Map

```
                     ┌─────────────────────────────────────────┐
                     │         Root Agent: StateStreetGECXDemo │
                     │  - Greeting & Intent Triage             │
                     │  - Account Identification (ACC-XXXX)    │
                     │  - OTP Issuance & MFA Validation        │
                     └────────────────────┬────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
┌──────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  Deal_Tickets_Agent  │      │ Receipt_of_Monies_Agent │      │    Escalation_Agent     │
│ - Trade execution    │      │ - Bank reconciliation   │      │ - Human handoffs        │
│ - ZILO Works status  │      │ - Value date / match    │      │ - Sentiment complaints  │
│ - ZILO Work Items    │      │ - SUBNR exception file  │      │ - Suspended accounts    │
│ - NIGO queue triage  │      │ - Cash matching status  │      │ - Warm Transfer Dossier │
└──────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

---

## Scenario 1: Processed & Settled Trade Inquiry
- **Agents Tested**: `StateStreetGECXDemo` (Root) $\rightarrow$ `Deal_Tickets_Agent`
- **Objective**: Verify standard authentication flow (MFA OTP) followed by seamless handoff to `Deal_Tickets_Agent` to query ZILO Works for an executed trade (`TRD-5001`).

### Turn-by-Turn Script

#### Turn 1: Initial Greeting & Identification
- **User Input (Copy & Paste)**:
```text
Hello, I am checking on the execution status of a trade for account ACC-1001.
```
- **Expected Agent Response**:
  - Welcomes the user to State Street Transfer Agency.
  - Recognizes account `ACC-1001` (Global Alpha Fund A / Meridian Capital Partners).
  - Triggers the MFA protocol and informs the user that a 6-digit One-Time Passcode (OTP) has been sent to their registered contact endpoint.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `search_account(account_no="ACC-1001")`
  - Tool Fired: `issue_otp_challenge(account_no="ACC-1001", channel="Chat", contact_input="ops@meridiancap.example")`
- **UI Visual Cue**: Telemetry panel updates with `Account: ACC-1001` and `MFA Status: Pending Challenge`.

#### Turn 2: OTP Verification & Intent Clarification
- **User Input (Copy & Paste)**:
```text
My verification code is 123456.
```
- **Expected Agent Response**:
  - Confirms OTP validation and authentication success.
  - Asks how it can assist with account `ACC-1001`.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `validate_otp_response(account_no="ACC-1001", otp_code="123456")`
  - Internal State: `authenticated = True`
- **UI Visual Cue**: Telemetry banner highlights green badge `✔ Verified (MFA Validated)`.

#### Turn 3: Trade Query & Dynamic Agent Transfer
- **User Input (Copy & Paste)**:
```text
Can you provide the status, trade date, and settlement amount for trade TRD-5001?
```
- **Expected Agent Response**:
  - Transfers control dynamically to `Deal_Tickets_Agent`.
  - Confirms trade `TRD-5001`:
    - **Status**: `Processed` (Settled)
    - **Trade Type**: Subscription
    - **Amount**: `$5,000,000.00 USD`
    - **Units**: `50,000.00` at NAV `$100.00`
    - **Trade Date**: `2026-03-10` | **Settlement Date**: `2026-03-12`
- **Behind the Scenes**:
  - Agent Transfer: `StateStreetGECXDemo` $\rightarrow$ `Deal_Tickets_Agent`
  - Tool Fired: `search_trade(account_no="ACC-1001", trade_ref="TRD-5001")`
- **UI Visual Cue**:
  - Agent Transfer pill: `🔄 Dynamic Agent Handoff: Control transferred to Deal_Tickets_Agent`
  - OpenAPI Tool badge: `⚡ OpenAPI Tool Request: search_trade`
  - Status badge: `Processed` in green/blue chip.

> **Testing Tip**: Valid default test OTPs in the mock layer are `123456`, `749201`, and `847291`.

---

## Scenario 2: NIGO Rejection & Exception Workflow Triage
- **Agents Tested**: `StateStreetGECXDemo` (Root) $\rightarrow$ `Deal_Tickets_Agent` $\rightarrow$ `Escalation_Agent` (Warm Handoff)
- **Objective**: Validate that a trade stuck in `NIGO` (Not In Good Order) missing authorized signatory is accurately retrieved from ZILO Work Items, explained clearly to the user, and offered for operational remediation.

### Turn-by-Turn Script

#### Turn 1: Account Identification
- **User Input (Copy & Paste)**:
```text
Hi, this is Ironclad Holdings. I need an update on trade TRD-5004 under account ACC-1004.
```
- **Expected Agent Response**:
  - Acknowledges Ironclad Holdings / BlackRock Prime Portfolios (`ACC-1004`).
  - Issues OTP security prompt.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `search_account(account_no="ACC-1004")`
  - Tool Fired: `issue_otp_challenge(account_no="ACC-1004", channel="Chat")`

#### Turn 2: OTP Verification
- **User Input (Copy & Paste)**:
```text
123456
```
- **Expected Agent Response**:
  - Verifies authentication.
  - Automatically acknowledges the requested reference `TRD-5004` or asks to proceed.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `validate_otp_response(account_no="ACC-1004", otp_code="123456")`
  - Agent Transfer: `StateStreetGECXDemo` $\rightarrow$ `Deal_Tickets_Agent`

#### Turn 3: NIGO Status Retrieval & Rejection Root Cause
- **User Input (Copy & Paste)**:
```text
Why has TRD-5004 not been executed yet? What is holding it up?
```
- **Expected Agent Response**:
  - Checks ZILO Works (returns pending/not completed) and inspects ZILO Work Items queue.
  - Reports that `TRD-5004` is in **NIGO** status.
  - Root Cause: **Missing Authorized Signatory** on subscription form.
  - Notes that work item `WI-9004` is assigned to Exception Processing and offers to route to an Investor Services specialist.
- **Behind the Scenes**:
  - Active Agent: `Deal_Tickets_Agent`
  - Tool Fired: `search_trade(account_no="ACC-1004", trade_ref="TRD-5004")`
  - Tool Fired: `search_work_item(account_no="ACC-1004", trade_ref="TRD-5004", queue="NIGO")`
- **UI Visual Cue**: Amber/Red exception indicator pill: `Queue: NIGO` | `Item Status: Held - Signature Required`.

#### Turn 4: Escalation to Human Desk for Signature Resolution
- **User Input (Copy & Paste)**:
```text
Please connect me with a representative who can send me the signatory remediation link.
```
- **Expected Agent Response**:
  - Triggers warm transfer to `Investor Services (Human)`.
  - Explains that the case notes, trade reference `TRD-5004`, and NIGO reason have been packaged into the specialist screen-pop.
- **Behind the Scenes**:
  - Active Agent: `Escalation_Agent`
  - Tool Fired: `escalate_interaction(target_queue="Investor Services (Human)", account_no="ACC-1004", reason="Trade TRD-5004 held in NIGO exception queue due to missing authorized signature")`
- **UI Visual Cue**:
  - Renders the **Agent Assist Warm Transfer Dossier Card** with:
    - **Target Desk**: `Investor Services (Human)`
    - **Reason**: `Trade TRD-5004 held in NIGO exception queue due to missing authorized signature`
    - **Suggested Specialist Action**: `Verify caller authority and provide secondary authorized signature submission link for NIGO remediation.`

> **Testing Tip**: Observe the trace toggle in the portal — the agent queries ZILO Works before searching ZILO Work Items per SOP Guardrails.

---

## Scenario 3: Cash Settlement & In-Flight Bank Reconciliation
- **Agents Tested**: `StateStreetGECXDemo` (Root) $\rightarrow$ `Receipt_of_Monies_Agent`
- **Objective**: Test deterministic cash reconciliation (CUJ 3) where trade settlement date is reached and bank reconciliation confirms monies have been matched (`TRD-5010`).

### Turn-by-Turn Script

#### Turn 1: Authentication
- **User Input (Copy & Paste)**:
```text
Hello, I need to check cash receipt and settlement for account ACC-1001. Passcode is 123456.
```
- **Expected Agent Response**:
  - Authenticates `ACC-1001` directly in one turn.
  - Welcomes Meridian Capital / Global Alpha Fund A and asks for the settlement reference or trade details.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `search_account(account_no="ACC-1001")`
  - Tool Fired: `validate_otp_response(account_no="ACC-1001", otp_code="123456")`
- **UI Visual Cue**: Auth status changes to `Verified`.

#### Turn 2: Receipt of Monies Query
- **User Input (Copy & Paste)**:
```text
Have you received the $2,000,000 cash wire for trade TRD-5010? Has it matched?
```
- **Expected Agent Response**:
  - Transits to `Receipt_of_Monies_Agent`.
  - Validates that `TRD-5010` is a qualifying trade in ZILO.
  - Queries Bank Reconciliation and confirms:
    - **Settlement State**: Monies Received & Settled (CUJ3-A)
    - **Received Amount**: `$2,000,000.00 USD`
    - **Received Date**: Today / Value Date matched
    - **Bank Rec Status**: `Matched` (SUBNR Flag: `No`)
- **Behind the Scenes**:
  - Agent Transfer: `StateStreetGECXDemo` $\rightarrow$ `Receipt_of_Monies_Agent`
  - Tool Fired: `execute_settlement_inquiry(account_no="ACC-1001", trade_ref="TRD-5010")`
  - Tool Fired: `search_bank_rec(account_no="ACC-1001", trade_ref="TRD-5010")`
- **UI Visual Cue**:
  - Transfer indicator: `Receipt_of_Monies_Agent`
  - Status Badge: `Bank Rec: Matched` (green pill).

> **Testing Tip**: The agent explicitly queries Bank Rec and receives a `Matched` record before stating funds have cleared.

---

## Scenario 4: Overdue Cash & SUBNR Sub-Narrative Discrepancy (Escalation to Cash Desk)
- **Agents Tested**: `StateStreetGECXDemo` $\rightarrow$ `Receipt_of_Monies_Agent` $\rightarrow$ `Escalation_Agent`
- **Objective**: Handle an exception where cash is past settlement date (SD+1 or greater), flagged on the SUBNR (Sub-Narrative) outstanding monies exception file, and must be proactively escalated to the Cash Management specialist team.

### Turn-by-Turn Script

#### Turn 1: Account & OTP Verification
- **User Input (Copy & Paste)**:
```text
Good morning, account ACC-1001, verification code 123456.
```
- **Expected Agent Response**:
  - Confirms authentication for account `ACC-1001`.
  - Asks how it can assist today.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo`
  - Tool Fired: `validate_otp_response(account_no="ACC-1001", otp_code="123456")`

#### Turn 2: Overdue Cash Check for TRD-5012
- **User Input (Copy & Paste)**:
```text
Can you verify if the $1,500,000 wire for trade TRD-5012 has settled? Our treasury team sent it yesterday.
```
- **Expected Agent Response**:
  - Hands off to `Receipt_of_Monies_Agent`.
  - Discovers `TRD-5012`:
    - Status in ZILO: `Unsettled`
    - Bank Rec: `Unmatched`
    - **SUBNR Flag**: `Yes` (Active exception on Sub-Narrative report, 1 day outstanding)
  - States transparently that the cash has passed its settlement date and is flagged on the outstanding monies file.
  - Automatically routes to `Escalation_Agent` targeting the **Cash Management Team**.
- **Behind the Scenes**:
  - Active Agent: `Receipt_of_Monies_Agent` $\rightarrow$ `Escalation_Agent`
  - Tool Fired: `search_bank_rec(account_no="ACC-1001", trade_ref="TRD-5012")`
  - Tool Fired: `escalate_interaction(target_queue="Cash Management", account_no="ACC-1001", reason="Settlement monies overdue at SD+1 with active SUBNR exception flag")`
- **UI Visual Cue**:
  - Warning callout: `SUBNR Flag: Active | Days Outstanding: 1`
  - **Warm Transfer Dossier Card**:
    - **Target Desk**: `Cash Management`
    - **Reason**: `Settlement monies overdue at SD+1 with active SUBNR exception flag`
    - **Suggested Specialist Action**: `Perform bank reconciliation trace in SWIFT/Fedwire settlement ledger for pending cash match.`

---

## Scenario 5: Immediate Sentiment Escalation / Suspended Account Restriction
- **Agents Tested**: `StateStreetGECXDemo` $\rightarrow$ `Escalation_Agent` (Direct bypass)
- **Objective**: Validate safety guardrails when a client exhibits high frustration or accesses a restricted/suspended account (`ACC-1005` - Apex Global Strategies / Vanguard Horizon). The agent must immediately triage to `Escalation_Agent` without trapping the customer in chatbot loops.

### Turn-by-Turn Script

#### Turn 1: Frustrated Entry on Suspended Account
- **User Input (Copy & Paste)**:
```text
This is completely unacceptable! Our multi-million dollar wire is blocked under account ACC-1005 and nobody is answering our calls. I demand to speak to a supervisor or senior manager right now!
```
- **Expected Agent Response**:
  - Immediately detects high negative sentiment and urgent compliance condition.
  - Looks up account `ACC-1005` and detects `Status: Suspended`.
  - De-escalates with an empathetic tone, avoids repetitive deflection, and initiates immediate warm transfer to **Account Management / Senior Specialist**.
- **Behind the Scenes**:
  - Active Agent: `StateStreetGECXDemo` $\rightarrow$ `Escalation_Agent`
  - Tool Fired: `search_account(account_no="ACC-1005")`
  - Tool Fired: `escalate_interaction(target_queue="Account Management", account_no="ACC-1005", reason="Account ACC-1005 profile is in Suspended status with high customer sentiment distress")`
- **UI Visual Cue**:
  - Telemetry updates to: `Agent: Escalation_Agent` | `Queue: Account Management`
  - Renders **Agent Assist: Live Warm Transfer Dossier Card**:
    - **Dossier Header**: `AGENT ASSIST: LIVE WARM TRANSFER DOSSIER`
    - **Account & Investor**: `ACC-1005 • Apex Global Strategies`
    - **Authentication State**: `Suspended Profile` (Amber badge)
    - **Target Desk**: `Account Management`
    - **Routing Mode**: `WARM_TRANSFER (Zero-Repetition)`
    - **Executive Summary**: Documents distress regarding blocked wire and suspended account status.
    - **Recommended Specialist Action**: `Verify institutional documentation to review suspended account restriction.`

---

### Quick Reference Matrix for Testers

| Scenario | Primary Agent | Target Entity | Expected Outcome | Visual UI Cue |
| :--- | :--- | :--- | :--- | :--- |
| **1. Settled Trade** | `Deal_Tickets_Agent` | `ACC-1001` / `TRD-5001` | Quoted $5M processed subscription | Green `Processed` badge, `search_trade` trace |
| **2. NIGO Rejection** | `Deal_Tickets_Agent` | `ACC-1004` / `TRD-5004` | Identified missing signature, offered rep | Amber `NIGO` pill, Warm Transfer Dossier |
| **3. Cash Matched** | `Receipt_of_Monies_Agent` | `ACC-1001` / `TRD-5010` | Verified $2M wire received and matched | `Matched` badge, `search_bank_rec` trace |
| **4. SUBNR Overdue** | `Receipt_of_Monies_Agent` $\rightarrow$ `Escalation_Agent` | `ACC-1001` / `TRD-5012` | Detected SUBNR exception, routed to Cash Desk | Red/Amber SUBNR tag, Cash Management Dossier |
| **5. Suspended / Frustration** | `Escalation_Agent` | `ACC-1005` | Immediate de-escalation & warm supervisor handoff | `Suspended Profile` tag, Account Mgmt Dossier |
