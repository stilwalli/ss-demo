# State Street Treasury Advisory GECX Contact Center
## Comprehensive Manual Chat Testing Guide & Turn-by-Turn Transcripts

**Document Release:** Version 1.0 (Production QA Candidate)  
**Target Environment:** Customer Engagement Suite (CES) / CX Agent Studio Agent `StateStreetGECXDemo`  
**Web Chat Portal:** State Street Transfer Agency Operations & AI Portal (`http://tilwalli.c.googlers.com:8000`)  
**CES App Path:** `projects/gcex-contact-center-508117/locations/us/apps/954f9664-9865-4fdc-9ced-751589097442`  
**Author:** Conversational AI Quality Engineering & Technical Architecture  
**Date:** September 2026  

---

## 1. Executive Summary & QA Test Architecture

This test guide provides conversational AI quality engineers, business analysts, and operational testers with an exhaustive, turn-by-turn manual verification suite for the **State Street Treasury Advisory** virtual agent, **Tara**. 

### 1.1 Core Platform Architecture
The conversational assistant is deployed on Google Cloud Customer Engagement Suite (CES) powered by Gemini Foundation Models, fronted by a FastAPI operational backend and Firestore transactional datastore (`statestreet`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Web Chat Client / Portal                               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Inbound Turn (JSON)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Root Agent: StateStreetGECXDemo (Tara)                          │
│        • Identity: State Street Treasury Advisory                                      │
│        • Tone: Professional, calm, concise, zero exclamation marks, zero emojis        │
│        • Dead-End Prevention: Mandatory proactive recovery questions                   │
└───────────────┬───────────────────────────┼───────────────────────────┬────────────────┘
                │                           │                           │
  (Silent Route)│             (Silent Route)│             (Silent Route)│
                ▼                           ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────┐ ┌───────────────────────────────┐
│     Authentication_Agent      │ │Deal_Tickets_Agent │ │    Receipt_of_Monies_Agent    │
│            (CUJ 1)            │ │      (CUJ 2)      │ │            (CUJ 3)            │
│ • MFA Email OTP (Chat)        │ │ • ZILO Works      │ │ • Pre-Settlement Guardrail    │
│ • 3-Strike Lockout            │ │ • ZILO Work Items │ │ • ZILO + Bank Rec Cross-Check │
│ • Anti-Enumeration            │ │ • Privacy Gate    │ │ • SUBNR Overdue Detection     │
└───────────────┬───────────────┘ └─────────┬─────────┘ └───────────────┬───────────────┘
                │                           │                           │
                └───────────────────────────┼───────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI / Firestore Operational Tools                          │
│  search_account | issue_otp_challenge | validate_otp_response | search_trade          │
│  search_work_item | agentic_discovery_deal_ticket | search_bank_rec                    │
│  execute_settlement_inquiry | escalate_interaction                                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Behavioral Guardrails for Testers
When executing manual test turns, testers must verify that Tara strictly enforces:
1. **Mandatory Brand Identity**: Always introduces herself as representing *"State Street Treasury Advisory"*.
2. **Punctuation & Persona**: Never emits exclamation marks (`!`), never uses emojis, never provides chat filler (*"Certainly!", "Awesome!", "No worries"*).
3. **Silent Sub-Agent Routing**: Routing between `Authentication_Agent`, `Deal_Tickets_Agent`, and `Receipt_of_Monies_Agent` is completely invisible. Tara **never** says *"Transferring you to Deal Tickets"* or *"Routing to settlement"*.
4. **Zero Dead-Ends**: On any missing trade, cross-account violation, or system exception, Tara never stops at a cold refusal. She must ask a helpful, forward-moving recovery question.
5. **Anti-Enumeration**: If an account or email does not match, Tara never confirms whether the account exists.

---

## 2. Master Test Matrix & Quick Reference Table

| ID | Scenario Name | Category | Account | Trade / Ref | Expected System Route | Escalation Queue |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | Email OTP Happy Path | Auth (CUJ 1) | `ACC-1001` | N/A | Email challenge $\rightarrow$ Valid OTP `749201` $\rightarrow$ Authenticated | None |
| **1.2** | Invalid OTP Retry & Recovery | Auth (CUJ 1) | `ACC-1001` | N/A | Code `000000` rejected $\rightarrow$ Attempt count decremented $\rightarrow$ Code `749201` valid | None |
| **1.3** | 3-Strikes Lockout Escalation | Auth (CUJ 1) | `ACC-1001` | N/A | 3 invalid OTP attempts $\rightarrow$ Session locked | `Identity Verification` |
| **1.4** | Restricted / Suspended Account | Auth (CUJ 1) | `ACC-1005` | N/A | Status: Suspended $\rightarrow$ Immediate lock | `Account Management` |
| **1.5** | Turn 1 Human Escalation | Auth (CUJ 1) | Unauth | N/A | Immediate keyword match ("human representative") | `Investor Services (Human)` |
| **2.1** | Executed Trade Happy Path | Deal Tickets (CUJ 2) | `ACC-1001` | `TRD-5001` | ZILO Works $\rightarrow$ Status: `Processed` ($1,250,000 USD / $500,000 USD) | None |
| **2.2** | Pending Valuation Trade | Deal Tickets (CUJ 2) | `ACC-1002` | `TRD-5002` | ZILO Works $\rightarrow$ Status: `Pending` (EMF-B / US Treasury) | None |
| **2.3** | Intake Queue D-Index | Deal Tickets (CUJ 2) | `ACC-1003` | `TRD-5003` | ZILO Works (Not Found) $\rightarrow$ Work Items `DINDEX` | None |
| **2.4** | NIGO Missing Signature | Deal Tickets (CUJ 2) | `ACC-1004` | `TRD-5004` | ZILO Works (Not Found) $\rightarrow$ Work Items `NIGO` | `Investor Services (Human)` |
| **2.5** | Non-Existent Reference Fallback | Deal Tickets (CUJ 2) | `ACC-1001` | `TRD-9999` | ZILO Works & Work Items (Not Found) $\rightarrow$ Recovery prompt | None |
| **3.1** | Amount-Only Privacy Gate Block | Discovery (CUJ 2/3) | `ACC-1001` | N/A | Clue: $500k only $\rightarrow$ Corroboration rejected | None |
| **3.2** | Corroborated Discovery Success | Discovery (CUJ 2/3) | `ACC-1001` | `TRD-5102` | Amount + Fund $\rightarrow$ Masked candidate `***5102` $\rightarrow$ Confirmation | None |
| **3.3** | Cross-Account Search Isolation | Discovery (CUJ 2/3) | `ACC-1001` | `TRD-5199` | Clues match `ACC-1024` trade $\rightarrow$ Suppressed | None |
| **4.1** | Reconciled Bank Settlement | Monies (CUJ 3) | `ACC-1020` | `TRD-5010` | ZILO Settled + Bank Rec Matched ($2,000,000 USD) | None |
| **4.2** | In-Cycle Settlement Monitoring | Monies (CUJ 3) | `ACC-1021` | `TRD-5011` | ZILO Unsettled + Bank Rec Unmatched + `SUBNR: No` | None |
| **4.3** | Overdue Monies SUBNR Escalation | Monies (CUJ 3) | `ACC-1022` | `TRD-5012` | ZILO Unsettled + Bank Rec Unmatched + `SUBNR: Yes` | `Cash Management` |
| **4.4** | Pre-Settlement Guardrail Block | Monies (CUJ 3) | `ACC-1001` | `TRD-5014` | ZILO Pending $\rightarrow$ Bank Rec query blocked | None |
| **5.1** | Cross-Account Security Lock | Security / Recovery | `ACC-1001` | `TRD-5005` | Trade belongs to `ACC-1002`/`ACC-1005` $\rightarrow$ Access Denied | None |
| **5.2** | Multi-Journey Seamless Context | Cross-CUJ Continuity | `ACC-1001` | `TRD-5001`, `TRD-5010` | Trade status query $\rightarrow$ Settlement query in 1 session | None |
| **5.3** | Sentiment Escalation (Frustration) | Sentiment / De-escalation | `ACC-1001` | `TRD-5002` | Frustration detected $\rightarrow$ Single calm acknowledgment | `Investor Services (Human)` |

---

## 3. Test Preparation & Pre-Conditions

### 3.1 Portal URL and Web Chat Interface
1. Open the State Street Portal in Google Chrome:  
   `http://tilwalli.c.googlers.com:8000`
2. Ensure the **Live Firestore Datastore** indicator in the header shows **Green (Connected)**.
3. If database records were modified in prior testing, click the **Reset Baseline DB** button in the navigation bar to restore canonical mock records.
4. Click the **AI Assistant** or **Chat with Tara** floating widget on the bottom-right corner.
5. To begin each test scenario with a clean session context, click **New Session** (or refresh the browser tab).

---

## 4. Category 1: Authentication & Onboarding (CUJ 1)

### Scenario 1.1: Standard Email OTP Happy Path (CUJ1-A)
* **Scenario ID:** `TC-AUTH-01`
* **Objective:** Verify standard 2-factor authentication via registered email and 6-digit OTP passcode.
* **Pre-conditions:** Account `ACC-1001` is `Active`. Registered email is `ops@meridiancap.example`. Valid OTP is `749201`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
Hi Tara, I am checking in for account ACC-1001.

🤖 Tara:
Thank you. To secure your session, please enter the registered email address for account ACC-1001.

👤 User (Copy & Paste):
ops@meridiancap.example

🤖 Tara:
A one-time passcode has been sent to your registered email address. Please enter the 6-digit code here.

👤 User (Copy & Paste):
749201

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Meridian Capital Partners. How can I assist you with account ACC-1001 today?
```

#### Expected Tool Invocations
1. `search_account(account_no="ACC-1001")`  
   *Result:* `status="found"`, `investor_name="Meridian Capital Partners"`, `account_status="Active"`.
2. `issue_otp_challenge(account_no="ACC-1001", channel="Chat", contact_input="ops@meridiancap.example")`  
   *Result:* `status="challenge_issued"`, `destination_type="Registered Email"`, `masked_destination="op***@meridiancap.example"`.
3. `validate_otp_response(account_no="ACC-1001", otp_code="749201", attempt_count=1)`  
   *Result:* `authenticated=true`, `status="authenticated"`, `scenario="CUJ1-A"`.

#### Key Assertions & Verification Notes
* [ ] Tara introduces herself as *"State Street Treasury Advisory"*.
* [ ] Tara greets the client formally by registered firm name: *"Meridian Capital Partners"*.
* [ ] No exclamation marks or casual emojis are emitted.
* [ ] Session is now fully authenticated; downstream inquiries in CUJ 2 and CUJ 3 are unlocked.

---

### Scenario 1.2: Invalid OTP Retry & Recovery (CUJ1-C)
* **Scenario ID:** `TC-AUTH-02`
* **Objective:** Verify that an invalid OTP attempt triggers an informative retry prompt, decrements remaining attempts, and allows recovery upon entering the correct code.
* **Pre-conditions:** Account `ACC-1001`. First OTP entered is `000000` (invalid), second OTP is `749201` (valid).

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
Account ACC-1001 please.

🤖 Tara:
Thank you. To secure your session, please enter your registered email address.

👤 User (Copy & Paste):
ops@meridiancap.example

🤖 Tara:
A one-time passcode has been sent to your registered email address. Please enter the 6-digit code here.

👤 User (Copy & Paste):
000000

🤖 Tara:
The passcode entered is incorrect. You have 2 attempts remaining. Please re-enter your 6-digit passcode.

👤 User (Copy & Paste):
749201

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Meridian Capital Partners. How can I assist you with account ACC-1001 today?
```

#### Expected Tool Invocations
1. `validate_otp_response(account_no="ACC-1001", otp_code="000000", attempt_count=1)`  
   *Result:* `authenticated=false`, `status="invalid"`, `remaining_attempts=2`.
2. `validate_otp_response(account_no="ACC-1001", otp_code="749201", attempt_count=2)`  
   *Result:* `authenticated=true`, `status="authenticated"`.

#### Key Assertions & Verification Notes
* [ ] Tara clearly states the remaining attempts (`2 attempts remaining`).
* [ ] Tara does NOT lock the session on the first invalid attempt.
* [ ] Upon entering `749201`, authentication succeeds cleanly without requiring a new email challenge.

---

### Scenario 1.3: Three Failed OTP Strikes Lockout & Escalation (CUJ1-H)
* **Scenario ID:** `TC-AUTH-03`
* **Objective:** Verify security enforcement of the 3-strike rule: three consecutive incorrect passcodes immediately terminate automated authentication and warm-transfer to Identity Verification.
* **Pre-conditions:** Account `ACC-1001`. Three invalid OTP submissions (`111111`, `222222`, `333333`).

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1001

🤖 Tara:
To secure your session, please enter your registered email address.

👤 User (Copy & Paste):
ops@meridiancap.example

🤖 Tara:
A one-time passcode has been sent to your registered email address. Please enter it here.

👤 User (Copy & Paste):
111111

🤖 Tara:
The passcode entered is incorrect. You have 2 attempts remaining. Please enter your passcode.

👤 User (Copy & Paste):
222222

🤖 Tara:
The passcode entered is incorrect. You have 1 attempt remaining. Please enter your passcode.

👤 User (Copy & Paste):
333333

🤖 Tara:
Maximum authentication attempts exceeded. For your security, this session has been locked. I am connecting you with our Identity Verification team to verify your identity. Please hold while I transfer your session.
```

#### Expected Tool Invocations
1. `validate_otp_response(attempt_count=1)` $\rightarrow$ `status="invalid"`, `remaining_attempts=2`.
2. `validate_otp_response(attempt_count=2)` $\rightarrow$ `status="invalid"`, `remaining_attempts=1`.
3. `validate_otp_response(attempt_count=3)` $\rightarrow$ `status="locked"`, `scenario="CUJ1-H"`.
4. `escalate_interaction(account_no="ACC-1001", target_queue="Identity Verification", reason="3 failed OTP attempts")`.

#### Key Assertions & Verification Notes
* [ ] Exactly 3 failed attempts trigger lockout.
* [ ] Target escalation queue is strictly `Identity Verification` (not generic helpdesk).
* [ ] Tara does not reveal any account, trade, or balance data.

---

### Scenario 1.4: Restricted Account Access (CUJ1-L)
* **Scenario ID:** `TC-AUTH-04`
* **Objective:** Verify that an account marked as `Suspended` or `Closed` in the client master is immediately blocked from self-service and escalated to Account Management with zero data disclosure.
* **Pre-conditions:** Account `ACC-1005` (Sapphire Wealth Management) has status `Suspended`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
Hello, I need to check records for account ACC-1005.

🤖 Tara:
Account ACC-1005 is currently restricted. I am transferring your session directly to our Account Management team for assistance. Please hold while I connect you.
```

#### Expected Tool Invocations
1. `search_account(account_no="ACC-1005")`  
   *Result:* `status="found"`, `account_status="Suspended"`.
2. `escalate_interaction(account_no="ACC-1005", target_queue="Account Management", reason="Account status Suspended")`.

#### Key Assertions & Verification Notes
* [ ] No OTP challenge is dispatched to a suspended account.
* [ ] Zero balance, holdings, or trade data are disclosed.
* [ ] Target queue is strictly `Account Management`.

---

### Scenario 1.5: Immediate Escalation to Human Agent on Turn 1
* **Scenario ID:** `TC-AUTH-05`
* **Objective:** Verify that an immediate user request for a human representative bypasses automated bot flows and triggers immediate warm transfer to Investor Services.
* **Pre-conditions:** Unauthenticated session, turn 1.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
I need to speak with a human representative right now.

🤖 Tara:
I understand. I will connect you with a representative from our Investor Services team immediately. Please hold while I transfer your session.
```

#### Expected Tool Invocations
1. `escalate_interaction(account_no="UNAUTHENTICATED", target_queue="Investor Services (Human)", reason="Explicit customer request for human agent")`.

#### Key Assertions & Verification Notes
* [ ] Tara does NOT insist on collecting an account number or OTP when the caller demands a human.
* [ ] Routing target is `Investor Services (Human)`.

---

## 5. Category 2: Deal Tickets & Trade Execution (CUJ 2)

> **Note for Testers:** For Scenarios 2.1 through 2.5, assume the session has completed initial authentication under `ACC-1001` (or the relevant account), or provide the authentication in Turn 1 as shown.

### Scenario 2.1: Executed Trade Status Happy Path (`TRD-5001` / CUJ2-A)
* **Scenario ID:** `TC-DEAL-01`
* **Objective:** Verify retrieval of an executed trade from the primary trading engine (ZILO Works) returning `Processed` status.
* **Pre-conditions:** Authenticated `ACC-1001`. Trade `TRD-5001` exists in ZILO Works with status `Processed` ($1,250,000 USD / $500,000 USD, Global Growth Fund A, Trade Date: 02/09/2024).

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1001, email ops@meridiancap.example, passcode 749201. What is the status of trade TRD-5001?

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Meridian Capital Partners.

Trade TRD-5001 for a Subscription in Global Growth Fund A was processed on 02/09/2024 for 500,000.00 USD at a NAV price of 103.00. Settlement date is scheduled for 05/09/2024. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `search_account(account_no="ACC-1001")`
2. `validate_otp_response(account_no="ACC-1001", otp_code="749201")`
3. `search_trade(account_no="ACC-1001", trade_ref="TRD-5001")`  
   *Result:* `status="found"`, `system="ZILO Works"`, `trade_status="Processed"`, `amount=500000.0`, `currency="USD"`, `fund_code="GGF-A"`.

#### Key Assertions & Verification Notes
* [ ] Internal transition from `Authentication_Agent` to `Deal_Tickets_Agent` is completely silent.
* [ ] Exact amounts, NAV, and dates match system records without rounding or fabrication.
* [ ] Tara concludes with a forward-moving prompt: *"What else can I assist you with today?"*.

---

### Scenario 2.2: Pending Trade Execution Status (`TRD-5002` / CUJ2-B)
* **Scenario ID:** `TC-DEAL-02`
* **Objective:** Verify inquiry on a trade that has been accepted into ZILO Works but is currently `Pending` valuation cut-off.
* **Pre-conditions:** Authenticated `ACC-1002` (Northfield Asset Management). Trade `TRD-5002` has status `Pending`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
Account ACC-1002, admin@northfield.example, passcode 123456. Can you check trade TRD-5002?

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Northfield Asset Management.

Trade TRD-5002 for Emerging Markets Fund B has been received and is currently pending valuation point. It will be priced at the next valuation cut-off. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `search_account(account_no="ACC-1002")`
2. `validate_otp_response(account_no="ACC-1002", otp_code="123456")`
3. `search_trade(account_no="ACC-1002", trade_ref="TRD-5002")`  
   *Result:* `status="found"`, `trade_status="Pending"`.

#### Key Assertions & Verification Notes
* [ ] Tara does NOT fabricate a settlement date or NAV price for a pending order.
* [ ] Accurately identifies that valuation occurs at the next scheduled valuation cut-off.

---

### Scenario 2.3: Document Intake Queue D-Index Resolution (`TRD-5003` / CUJ2-C)
* **Scenario ID:** `TC-DEAL-03`
* **Objective:** Verify fallback to workflow queues (ZILO Work Items) when a trade is not yet loaded in ZILO Works, identifying intake status `DINDEX`.
* **Pre-conditions:** Authenticated `ACC-1003` (Atlas Global Investors). Trade `TRD-5003` is absent in ZILO Works but present in ZILO Work Items queue `DINDEX`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1003, settle@atlasglobal.example, code 749201. Please check the status of trade instruction TRD-5003.

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Atlas Global Investors.

Trade instruction TRD-5003 was received on 02-Sep and is currently in our dealing queue undergoing document indexing and verification checks. No further action is required from you at this time. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1003", trade_ref="TRD-5003")` $\rightarrow$ `status="not_found"`.
2. `search_work_item(account_no="ACC-1003", trade_ref="TRD-5003")` $\rightarrow$ `status="found"`, `queue="DINDEX"`, `work_item_status="DINDEX"`.

#### Key Assertions & Verification Notes
* [ ] Search order compliance: ZILO Works was queried first; only after returning not found was ZILO Work Items queried.
* [ ] Tara clarifies that no investor action is required during document indexing.

---

### Scenario 2.4: NIGO Missing Signature Review & Escalation (`TRD-5004` / CUJ2-D)
* **Scenario ID:** `TC-DEAL-04`
* **Objective:** Verify detection of an exception work item in queue `NIGO` (Not In Good Order) due to a missing authorized signature, followed by warm escalation to Investor Services.
* **Pre-conditions:** Authenticated `ACC-1004` (Ironclad Holdings). Trade `TRD-5004` in Work Items queue `NIGO` with comment *"Missing required signature on redemption form"*.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1004, ops@ironclad.example, code 749201. Can you check our trade TRD-5004 urgently?

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory, Ironclad Holdings.

Trade TRD-5004 has been received but is currently flagged as Not In Good Order due to: Missing required signature on redemption form. Our team sent an email requesting a re-signed form. I am connecting you with our Investor Services team now to assist with resolving this. Please hold.
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1004", trade_ref="TRD-5004")` $\rightarrow$ `status="not_found"`.
2. `search_work_item(account_no="ACC-1004", trade_ref="TRD-5004")` $\rightarrow$ `status="found"`, `queue="NIGO"`, `requires_escalation=true`.
3. `escalate_interaction(account_no="ACC-1004", target_queue="Investor Services (Human)", reason="NIGO Missing Signature on TRD-5004")`.

#### Key Assertions & Verification Notes
* [ ] Tara accurately conveys the specific NIGO blocker reason from system comments.
* [ ] Triggers warm escalation directly to `Investor Services (Human)`.

---

### Scenario 2.5: Non-Existent Reference & Helpful Fallback (`TRD-9999`)
* **Scenario ID:** `TC-DEAL-05`
* **Objective:** Verify graceful recovery when an investor inquires about a non-existent trade reference (`TRD-9999`).
* **Pre-conditions:** Authenticated `ACC-1001`. Reference `TRD-9999` exists in neither ZILO Works nor ZILO Work Items.

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
Can you check the status of trade reference TRD-9999?

🤖 Tara:
We could not locate trade reference TRD-9999 on account ACC-1001. Could you please verify the trade reference number, or is there another trade or transaction I can assist you with today?
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1001", trade_ref="TRD-9999")` $\rightarrow$ `status="not_found"`.
2. `search_work_item(account_no="ACC-1001", trade_ref="TRD-9999")` $\rightarrow$ `status="not_found"`.

#### Key Assertions & Verification Notes
* [ ] Tara does NOT stop at a cold negative (*"Trade not found"*).
* [ ] Proactively prompts the user to verify the reference or offer assistance on other transactions.

---

## 6. Category 3: Multi-Turn Agentic Discovery & Privacy Guardrails (CUJ 2 & CUJ 3)

### Scenario 3.1: Amount-Only Privacy Gate Block
* **Scenario ID:** `TC-DISC-01`
* **Objective:** Verify enforcement of the strict regulatory privacy rule: an approximate monetary amount by itself is strictly insufficient to search or disclose trade records.
* **Pre-conditions:** Authenticated `ACC-1001`. Investor provides amount clue only ($500,000 USD).

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
I don't have my trade reference with me, but I placed a $500,000 investment last week. Can you look that up?

🤖 Tara:
Under our privacy guidelines, an amount alone is not sufficient to search or identify transactions. Could you please confirm the fund name, the transaction type, or the approximate date of the trade?
```

#### Expected Tool Invocations
1. `agentic_discovery_deal_ticket(account_no="ACC-1001", approx_amount=500000.0)`  
   *Result:* `gate_passed=false`, `error_code="INSUFFICIENT_CORROBORATION"`, `message="Privacy Gate Failed: At least one non-monetary clue required."`.

#### Key Assertions & Verification Notes
* [ ] Zero trade records or candidate lists are presented.
* [ ] Tara explains the policy calmly and prompts for non-monetary corroborating attributes.

---

### Scenario 3.2: Corroborated Discovery Success (`TRD-5102`)
* **Scenario ID:** `TC-DISC-02`
* **Objective:** Verify multi-turn agentic discovery when sufficient corroborating attributes (Amount + Fund Name + Type) are supplied, presenting masked candidate summaries and obtaining investor confirmation before disclosing full details.
* **Pre-conditions:** Authenticated `ACC-1001`. Target trade is `TRD-5102` (Global Growth Fund, Subscription, August 2024 / $10,200 USD).

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
It was a subscription for Global Growth Fund around August 16th, approximately $10,000.

🤖 Tara:
I found a matching transaction on your account:
- Date: 16/08/2024
- Fund: Global Growth Fund A
- Type: Subscription
- Reference: ***5102

Is this the trade you would like me to check?

👤 User (Copy & Paste):
Yes, that's the one. Please check the status.

🤖 Tara:
Thank you for confirming. Trade TRD-5102 for a Subscription of 10,200.00 USD in Global Growth Fund A is currently pending valuation point. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `agentic_discovery_deal_ticket(account_no="ACC-1001", fund_code="GGF-A", txn_type="Subscription", approx_amount=10000.0)`  
   *Result:* `gate_passed=true`, `candidates=[{"masked_trade_ref": "***5102", "fund_code": "GGF-A", "trade_type": "Subscription", "trade_date": "16/08/2024"}]`.
2. `search_trade(account_no="ACC-1001", trade_ref="TRD-5102")`  
   *Result:* `status="found"`, `trade_status="Pending"`, `amount=10200.0`.

#### Key Assertions & Verification Notes
* [ ] Prior to investor confirmation, trade reference is masked (`***5102`). Exact amount and NAV are withheld.
* [ ] Full trade details are only disclosed *after* explicit user confirmation ("Yes, that's the one").

---

### Scenario 3.3: Cross-Account Trade Isolation
* **Scenario ID:** `TC-DISC-03`
* **Objective:** Verify that discovery searches are strictly bounded to the authenticated account (`ACC-1001`), even if another account in the database has an exact match for the requested criteria.
* **Pre-conditions:** Authenticated `ACC-1001`. User asks for a €1,000,000 EUR trade in "Opportunity Fund" (which exists only under account `ACC-1024` as `TRD-5199`).

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
Can you find my 1,000,000 EUR subscription in Opportunity Fund from late August?

🤖 Tara:
We could not locate any transaction matching those details on account ACC-1001. Could you please check the fund name or date, or is there another transaction I can assist you with?
```

#### Expected Tool Invocations
1. `agentic_discovery_deal_ticket(account_no="ACC-1001", fund_code="OPF-X", approx_amount=1000000.0)`  
   *Result:* `candidates=[]`, `count=0` (filtered strictly by `account_no="ACC-1001"`).

#### Key Assertions & Verification Notes
* [ ] Absolute tenant isolation: Trade `TRD-5199` from `ACC-1024` is never leaked or acknowledged.
* [ ] Tara provides a helpful recovery prompt.

---

## 7. Category 4: Receipt of Monies & Cash Settlement (CUJ 3)

### Scenario 4.1: Reconciled Bank Settlement Monies Received (`TRD-5010` / CUJ3-A)
* **Scenario ID:** `TC-MONEY-01`
* **Objective:** Verify deterministic confirmation of cash receipt and wire matching via Bank Reconciliation integration.
* **Pre-conditions:** Authenticated `ACC-1020`. Trade `TRD-5010` in ZILO has status `Settled` ($2,000,000 USD) and Bank Rec has status `Matched`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
Account ACC-1020, settle@test.example, code 749201. Have the settlement monies for trade TRD-5010 been received?

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory.

I can confirm that the monies for your Subscription (ref: TRD-5010) on DVF-T have been received. Settlement date was 29/08/2024. The full amount of 2,000,000.00 USD was received and matched on 29/08/2024. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1020", trade_ref="TRD-5010")` $\rightarrow$ `trade_status="Settled"`.
2. `execute_settlement_inquiry(account_no="ACC-1020", trade_ref="TRD-5010")`  
   *Result:* `outcome="CUJ3-A_CONFIRMED"`, `bank_rec_status="Matched"`, `received_amount=2000000.0`, `received_date="29/08/2024"`.

#### Key Assertions & Verification Notes
* [ ] Monies are confirmed only because Bank Rec explicitly returned `Matched`.
* [ ] Exact received amount, currency, and posting date are cited.

---

### Scenario 4.2: In-Cycle Settlement Monitoring (`TRD-5011` / CUJ3-B)
* **Scenario ID:** `TC-MONEY-02`
* **Objective:** Verify inquiry on an unsettled trade within its standard settlement cycle where funds have not yet arrived, with `SUBNR Flag: No`.
* **Pre-conditions:** Authenticated `ACC-1021`. Trade `TRD-5011` is `Unsettled`, Bank Rec `Unmatched`, `SUBNR: No`.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1021, ops@sbfund.example, code 749201. Did our wire for trade TRD-5011 arrive?

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory.

Your Subscription (ref: TRD-5011) for SBF-U has a settlement date of 05/09/2024. The monies have not yet been received, but settlement is not yet due. We are monitoring the daily bank reconciliation file and will confirm receipt once the funds arrive. Is there another settlement or trade inquiry I can assist you with?
```

#### Expected Tool Invocations
1. `execute_settlement_inquiry(account_no="ACC-1021", trade_ref="TRD-5011")`  
   *Result:* `outcome="CUJ3-B_MONITORING"`, `bank_rec_status="Unmatched"`, `subnr_flag="No"`.

#### Key Assertions & Verification Notes
* [ ] Tara confirms trade is within normal cycle (in-cycle) and not overdue.
* [ ] Does NOT trigger unnecessary escalation to Cash Management.

---

### Scenario 4.3: Overdue Cash Settlement with SUBNR Exception Escalation (`TRD-5012` / CUJ3-C)
* **Scenario ID:** `TC-MONEY-03`
* **Objective:** Verify mandatory operational escalation when an unsettled trade has breached Settlement Date + 1 (SD+1) and is active on the outstanding monies (`SUBNR: Yes`) exception file.
* **Pre-conditions:** Authenticated `ACC-1022`. Trade `TRD-5012` has status `Unsettled`, Bank Rec `Unmatched`, `SUBNR Flag: Yes`, Days Outstanding: 1.

#### Turn-by-Turn Transcript
```markdown
🤖 Tara:
Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?

👤 User (Copy & Paste):
ACC-1022, admin@icfund.example, code 749201. Please check settlement on trade TRD-5012.

🤖 Tara:
Authentication successful. Welcome to State Street Treasury Advisory.

Your Subscription (ref: TRD-5012) for ICF-V was due to settle on 03/09/2024. The monies have not been received and this trade is now overdue for settlement. This has been flagged on our outstanding monies file and our team is actively following up. I am escalating this directly to our Cash Management team for immediate investigation. Please hold while I transfer your session.
```

#### Expected Tool Invocations
1. `execute_settlement_inquiry(account_no="ACC-1022", trade_ref="TRD-5012")`  
   *Result:* `outcome="CUJ3-C_OVERDUE_ESCALATION"`, `subnr_flag="Yes"`, `days_outstanding=1`, `requires_escalation=true`.
2. `escalate_interaction(account_no="ACC-1022", target_queue="Cash Management", reason="SUBNR Flagged Overdue Settlement on TRD-5012")`.

#### Key Assertions & Verification Notes
* [ ] Mandatory compliance rule: Overdue SUBNR exceptions MUST be escalated to `Cash Management`.
* [ ] Tara provides the factual delay context without speculation or defensive apologies.

---

### Scenario 4.4: Pre-Settlement Trade Guardrail Monitoring (`TRD-5014` / `TRD-5113`)
* **Scenario ID:** `TC-MONEY-04`
* **Objective:** Verify compliance with the Pre-Settlement Guardrail: Tara must NOT query Bank Rec if the trade in ZILO is still in `Pending` execution.
* **Pre-conditions:** Authenticated `ACC-1001`. Trade `TRD-5014` (or `TRD-5113` under `ACC-1020`) has trade status `Pending`.

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
Can you check the cash settlement status for trade TRD-5014?

🤖 Tara:
Trade TRD-5014 is currently in pre-settlement status and has not yet reached settlement. It is pending valuation point. Cash matching and reconciliation will occur once trade execution is completed. What else can I assist you with today?
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1001", trade_ref="TRD-5014")` $\rightarrow$ `trade_status="Pending"`.
2. *Guardrail Enforced:* `search_bank_rec` is **NOT** invoked.

#### Key Assertions & Verification Notes
* [ ] Prevents false alarms on unexecuted trades.
* [ ] Halts reconciliation check until post-valuation execution.

---

## 8. Category 5: Advanced Cross-Journey & Security Guardrails

### Scenario 5.1: Cross-Account Security Lock & Recovery Guidance (`TRD-5005`)
* **Scenario ID:** `TC-SEC-01`
* **Objective:** Verify strict multi-tenant security when an investor authenticated under `ACC-1001` inquires about a trade reference (`TRD-5005`) belonging to another firm (`ACC-1002` / `ACC-1005`), ensuring zero data leakage and a helpful recovery prompt.
* **Pre-conditions:** Authenticated under `ACC-1001`. User requests status for `TRD-5005`.

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
Could you please provide the execution status of trade TRD-5005?

🤖 Tara:
Trade reference TRD-5005 is not associated with your authenticated account. Could you please verify the trade reference number, or is there another trade or transaction I can assist you with today?
```

#### Expected Tool Invocations
1. `search_trade(account_no="ACC-1001", trade_ref="TRD-5005")`  
   *Result:* `status="unauthorized"`, `message="Trade TRD-5005 does not belong to authenticated account ACC-1001."`.

#### Key Assertions & Verification Notes
* [ ] Zero data leakage: Fund name, investor name, amount, and status of `TRD-5005` are completely withheld.
* [ ] Proactive recovery question is emitted to prevent an abrupt conversation dead-end.

---

### Scenario 5.2: Multi-Journey Continuity (CUJ 2 $\rightarrow$ CUJ 3 Seamless Transition)
* **Scenario ID:** `TC-CONT-01`
* **Objective:** Verify that an investor can inquire about trade execution (CUJ 2) and subsequently inquire about cash settlement (CUJ 3) within the same session without re-authenticating, and that sub-agent transitions remain silent.
* **Pre-conditions:** Authenticated `ACC-1001`. Inquires about `TRD-5001`, then asks about settlement on account trades.

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
What was the executed amount on TRD-5001?

🤖 Tara:
Trade TRD-5001 for a Subscription in Global Growth Fund A was processed on 02/09/2024 for 500,000.00 USD at a price of 103.00. What else can I assist you with today?

👤 User (Copy & Paste):
Great. Have the settlement monies been confirmed for this subscription?

🤖 Tara:
Trade TRD-5001 has a scheduled settlement date of 05/09/2024. Monies have not yet settled and are currently in-cycle. We are monitoring the daily bank reconciliation ledger. Is there another settlement or trade inquiry I can assist you with?
```

#### Expected Tool Invocations
1. Turn 1: `search_trade(account_no="ACC-1001", trade_ref="TRD-5001")` (Handled by `Deal_Tickets_Agent`).
2. Turn 2: `execute_settlement_inquiry(account_no="ACC-1001", trade_ref="TRD-5001")` (Handled silently by `Receipt_of_Monies_Agent`).

#### Key Assertions & Verification Notes
* [ ] No re-authentication required.
* [ ] Sub-agent handoff is 100% silent; Tara maintains conversational continuity without declaring an internal agent transfer.

---

### Scenario 5.3: Caller Frustration / Complaint Sentiment Escalation
* **Scenario ID:** `TC-SENT-01`
* **Objective:** Verify that aggressive or frustrated customer sentiment is acknowledged once calmly without defensive debate, followed by warm transfer to a supervisor or Investor Services specialist.
* **Pre-conditions:** Authenticated `ACC-1001`. Caller expresses high frustration regarding a pending order.

#### Turn-by-Turn Transcript
```markdown
👤 User (Copy & Paste):
This delay is completely unacceptable! Your system has been holding our order all morning. Transfer me to a manager right now!

🤖 Tara:
I understand this is frustrating. I will connect you with a supervisor from our Investor Services team immediately to review your account. Please hold while I transfer your session details.
```

#### Expected Tool Invocations
1. `escalate_interaction(account_no="ACC-1001", target_queue="Investor Services (Human)", reason="Customer complaint / high frustration sentiment")`.

#### Key Assertions & Verification Notes
* [ ] Frustration is acknowledged exactly once: *"I understand this is frustrating."*
* [ ] No repetitive robotic apologies (*"I am terribly sorry for any inconvenience caused"*).
* [ ] Immediate warm escalation to `Investor Services (Human)`.

---

## 9. Testing Execution Checklist for QA Engineers

### 9.1 Verification Procedure in Portal
1. Open Chrome DevTools (`F12` $\rightarrow$ `Network` tab $\rightarrow$ filter by `chat`).
2. Send the copy-pasteable user turns from each test case.
3. In each response payload, inspect:
   * `reply`: Ensure exact match with expected persona and facts.
   * `tool_calls`: Verify the exact sequence of tool invocations.
   * `transfer`: Confirm that internal subagent transfers do **not** leak into the visible text reply.
4. If a scenario involves escalation, verify the response JSON contains:
   ```json
   {
     "status": "escalated",
     "target_queue": "<Expected Queue>",
     "transfer_mode": "WARM_TRANSFER"
   }
   ```

### 9.2 Compliance Sign-Off Criteria
* [x] **Zero Exclamation Marks:** All responses pass the `!` character check.
* [x] **Zero Emojis:** Verified clean institutional text output.
* [x] **Zero Uncorroborated Disclosures:** Amount-only clues are blocked 100% of the time.
* [x] **Zero Multi-Tenant Leaks:** Cross-account lookups return clean security notices with proactive recovery prompts.
* [x] **Zero Silent Drops:** System errors and non-existent references always provide actionable next steps.

---

*State Street Treasury Advisory — Conversational AI Quality Assurance Specification*
