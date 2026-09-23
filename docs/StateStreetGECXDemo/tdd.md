# Technical Design Document (TDD): StateStreetGECXDemo

**Application Name:** StateStreetGECXDemo  
**Version:** 1.0.0 (Production Candidate)  
**Target Platform:** Google Cloud Customer Engagement Suite (CES) / CX Agent Studio (CXAS)  
**Persona:** Tara — State Street Treasury Advisory  
**Channels:** Inbound Telephony (Voice US DID) & Web Chat Widget  

---

## 1. System Architecture & Component Breakdown

The application is structured as a **Single GECX Multi-Agent Application** consisting of an Orchestrator and three specialized sub-agents. Inter-agent routing is **completely silent and suppressed** to the user.

```
                              ┌───────────────────────────────────┐
                              │     StateStreetGECXDemo (Root)    │
                              │     Global Instructions & Tone     │
                              └─────────────────┬─────────────────┘
                                                │ (Silent Sub-Agent Routing)
                     ┌──────────────────────────┼──────────────────────────┐
                     ▼                          ▼                          ▼
          ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
          │ Authentication_Agent│    │  Deal_Tickets_Agent │    │Receipt_Monies_Agent │
          │   (CUJ 1: MFA OTP)  │    │ (CUJ 2: ZILO Trades)│    │(CUJ 3: Bank Rec Cash│
          └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### 1.1 Global Instructions (App Level)
* **Identity:** State Street Treasury Advisory.
* **Greeting:** *"Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?"*
* **Tone Guardrails:** Zero exclamation marks, zero emojis, factual, professional, acknowledge frustration once.
* **Silent Handoff Directive:** When transitioning between internal sub-agents, never say *"Transferring you..."* or announce internal routing. The receiving agent responds immediately to user intent.

### 1.2 Sub-Agents (Playbooks)
1. **`Authentication_Agent` (CUJ 1)**:
   - Evaluates account status (`Active`, `Suspended`, `Closed`).
   - Chat: Email match $\rightarrow$ 6-digit OTP $\rightarrow$ 5 min expiry $\rightarrow$ validate.
   - Voice: Incoming ANI phone match $\rightarrow$ SMS OTP $\rightarrow$ validate.
   - Enforces 3-strike lockout and rapid-guessing security checks.
2. **`Deal_Tickets_Agent` (CUJ 2)**:
   - Checks ZILO Works for `Processed` (CUJ2-A) and `Pending` (CUJ2-B).
   - Fallback to ZILO Work Items for `DINDEX` (CUJ2-C) and `NIGO` (CUJ2-D signature discrepancy).
   - Unknown trade reference (`CUJ2-E`): Prompts Transaction Type, Date, Fund; enforces 2-clue privacy gate before presenting masked candidates (`***5102`).
3. **`Receipt_of_Monies_Agent` (CUJ 3)**:
   - Pre-settlement check in ZILO: If pending, halts Bank Rec query.
   - Cross-checks ZILO Trades + Bank Reconciliation.
   - Evaluates `Bank Rec Status` and `SUBNR Flag`:
     - `Matched` $\rightarrow$ Monies received (CUJ3-A).
     - `Unmatched` & `SUBNR: No` $\rightarrow$ In-cycle monitoring (CUJ3-B).
     - `Unmatched` & `SUBNR: Yes` $\rightarrow$ Overdue at SD+1 (CUJ3-C) $\rightarrow$ Escalate to Cash Management.
   - Unknown reference (`CUJ3-D`): Withholds Bank Rec query until candidate confirmed.

---

## 2. Escalation Queue Specifications

All non-automated or exception paths route to one of the 6 specialized targets defined in V4:
1. `Identity Verification`: Unverified phone/email, 3 failed OTPs.
2. `Security`: Rapid automated guessing, replay attempts.
3. `Technical Support`: Backend timeouts or gateway errors.
4. `Account Management`: Suspended (`ACC-1005`) or Closed (`ACC-1006`) accounts.
5. `Cash Management`: Overdue monies flagged on SUBNR at SD+1 (`TRD-5012`).
6. `Investor Services (Human)`: Explicit caller request for human or complaint sentiment.
