# State Street Institutional Transfer Agency AI Contact Center
## Non-Functional Requirements (NFR) Architectural Research & Solution Blueprint
### Google Cloud Customer Engagement Suite (CES / GECX), CX Agent Studio (CXAS), CCAI Insights & Agent Assist

**Author:** Enterprise Cloud Solutions Architecture Team  
**Audience:** Shashank Tilwalli (Google Cloud Conversational AI Specialist), Sriram Piratla (VP Data & AI, State Street), Mark Healy (Business Sponsor / Product, State Street), Rob Cox (Google Cloud)  
**Date:** September 22, 2026  
**Document Status:** Final Architectural Research Deliverable  
**Target Milestone:** Executive Demonstration & Dry Runs (October 5, 2026) / Enterprise Production Roadmap

---

## Executive Summary

State Street Corporation’s Transfer Agency (TA) division is executing a foundational modernization: transitioning core shareholder accounting, workflow distribution, and cash reconciliation from legacy platforms (**iFAST**, **AWD - Automated Work Distributor**, and manual bank reconciliation spreadsheets) to **ZILO (Zilo Works)** and **Zilo Work**.

To front this modern ecosystem, State Street is deploying Google Cloud’s **Customer Engagement Suite (CES / GECX)**—incorporating **CX Agent Studio (CXAS)**, **Google Telephony Platform (GTP)**, **Contact Center AI (CCAI) Insights**, and **Agent Assist**. 

On September 16, 2026, Business Sponsor **Mark Healy** formally signed off on the project scope and established the official priority ranking for **18 Non-Functional Requirements (NFRs)** across 4 categories:
1. **Omni Channel** (5 requirements)
2. **Agentic & Conversational AI** (4 requirements)
3. **Analytics & Insights** (4 requirements)
4. **Responsible AI, Privacy & Compliance** (5 requirements)

This architectural findings report delivers an in-depth technical analysis for each of the 18 requirements. For every requirement, it articulates:
- **Scope & Meaning in State Street Context** (institutional fund administration, dealing cut-offs, unitholder servicing, cash reconciliation).
- **Google Cloud / GECX Solution Architecture** (exact Google Cloud products, protos, APIs, network topologies, and CCaaS integration patterns).
- **Implementation Strategy & Complexity** (OOTB vs. Custom integration, step-by-step technical realization).
- **POC vs. Production Roadmap** (October 5, 2026 POC deliverables vs. Day-2 / Production enterprise rollout).

---

## Master Requirements Traceability & Priority Matrix

| # | Requirement Name | Category | Healy Priority | Architecture Strategy | Primary Google Cloud / Partner Technologies | POC Status (Oct 5) | Production Target |
|:---:|:---|:---|:---:|:---|:---|:---:|:---:|
| **1** | Omnichannel Routing | Omni Channel | **HIGH** | Hybrid | CXAS Voice Gateway (GTP), CES Web Messenger, SIP REFER / UUI, Genesys Cloud / Cisco CUBE | Dual-channel parity (US Voice + Web Chat) | Multi-region SIP peering, cross-channel state persistence |
| **2** | Omni Channel Outbound Campaigns | Omni Channel | **LOW** | Custom Integration | Cloud Run, Eventarc, Pub/Sub, CXAS Outbound Telephony API / CCaaS Dialer | Deferred (Architectural blueprint only) | Event-driven automated SUBNR / NIGO debtor outreach |
| **3** | Skills and Proficiency Routing | Omni Channel | **MEDIUM** | Hybrid | CXAS Conditional Routes, `LIVE_AGENT_HANDOFF`, SIP UUI Headers, Genesys ACD / Bullseye | Structured escalation payloads to simulated queues | Enterprise SIP UUI skill mapping to Cash Mgmt & Dealing Ops |
| **4** | Task Management | Omni Channel | **HIGH** | Custom Integration | CXAS Agentic Tools, Cloud Run middleware, Zilo Work API (`createWorkItem`, `updateQueue`) | Mock Zilo Work queue checks (`DINDEX`, `NIGO`) | Bi-directional Zilo Work API CRUD + SLA escalation |
| **5** | Rules Engine | Omni Channel | **HIGH** | Hybrid | CXAS Condition Routes, Deterministic Tool Gates, CEL Autolabeling Rules | Hardcoded 2-clue privacy gate, NIGO, & SD+1 SUBNR rules | Enterprise CEL / Drools Business Rule Engine service |
| **6** | Authentication-Aware Personalization | Agentic & Conv. AI | **MEDIUM** | Hybrid | CXAS Session Params, Zilo Client Master API, Okta/Ping IAM, Dynamic Prompts | Mock MFA & account lookup, personalized greeting | Enterprise Institutional SSO, voice biometrics, OAuth2 tokens |
| **7** | Content Safety and Policy Guardrails | Agentic & Conv. AI | **MEDIUM** | OOTB + Prompts | CXAS Safety Settings, Vertex AI Guardrails / Model Armor, Negative Prompt Constraints | "Tara" persona constraints (no emojis/exclamations, grounded) | Google Model Armor proxy, automated guardrail regression tests |
| **8** | Conversation Summarization and Case Notes | Agentic & Conv. AI | **MEDIUM** | OOTB | Google Agent Assist Summarization Generator (`generator.proto`), CRM CTI Connector | Auto-generated structured escalation summary in UI | Real-time CTI push to Salesforce Service Cloud / Genesys Workspace |
| **9** | Multilingual Understanding and Generation | Agentic & Conv. AI | **LOW** | OOTB | CXAS Multi-language Engine, Gemini multilingual reasoning, Cloud STT/TTS | English-only (`en-US` / `en-GB`) | Global UCITS hub support (French, German, Italian, Japanese) |
| **10** | Call Recording | Analytics & Insights | **HIGH** | Hybrid | GTP `SessionAudioRecorder.cc` (GCS) or SBC SIPREC (RFC 7865/7866) to Verint/NICE | Native GTP GCS recording for virtual agent interactions | SBC SIPREC dual-forking to Verint/NICE with WORM GCS archive |
| **11** | Data Redaction | Analytics & Insights | **LOW** | OOTB | Cloud Sensitive Data Protection (DLP v2 API), CXAS Security Settings | Basic regex DLP masking in agent security settings | Full Cloud DLP de-identification templates across audio & text |
| **12** | Real-Time and Historical Analytics | Analytics & Insights | **HIGH** | OOTB | CCAI Insights Ingestion Pipeline, BigQuery Streaming Export, CEL Autolabeling | Active CCAI Insights project with POC call telemetry | Enterprise BigQuery dataset, streaming Pub/Sub, Looker models |
| **13** | Dashboards | Analytics & Insights | **HIGH** | OOTB | CCAI Insights Configurable Dashboards (`dashboards.yaml`), Vega-Lite, Looker Studio | Executive KPI Dashboard (Volume, Containment, AHT, Escalation) | Multi-tenant executive reporting, scheduled SLA digests |
| **14** | Regulatory Compliance in Local Markets | Responsible AI | **MEDIUM** | Governance & Config | Regional Resource Pinning (`us-central1`, `europe-west1`), VPC-SC, CMEK, SOC1/2 | US region deployment, architectural compliance blueprint | Multi-region EU data residency (DORA / UCITS / CSSF compliant) |
| **15** | Data Classification and Handling | Responsible AI | **MEDIUM** | Architecture Pattern | Strict Account Partitioning, IAM Least Privilege, Google Cloud Dataplex | Strict account filtering enforced in tool execution | Dataplex policy tags, automated metadata classification |
| **16** | PII / PCI Detection and Masking | Responsible AI | **MEDIUM** | Hybrid | Cloud DLP Inspect/Deidentify Templates, Algorithmic Candidate Masking | Masked candidate references (`***5102`), test DLP filters | Production Cloud DLP tokenization and redaction pipeline |
| **17** | Privacy Notice and Customer Consent | Responsible AI | **LOW** | OOTB | CXAS Default Welcome Flow Fulfillment, Conditional Transfer Routes | Mandatory recording disclaimer in "Tara" greeting | Dynamic regional consent logic based on ANI / geography |
| **18** | Audit Logging and Monitoring | Responsible AI | **LOW** | OOTB | Cloud Logging, Cloud Audit Logs, BigQuery Sink, Cloud Monitoring Alerts | Standard Cloud Logging and BigQuery telemetry export | Enterprise SIEM (Splunk) forwarder, 7-year WORM audit retention |

---

## Section 1: Omni Channel Architecture

```
                  ┌────────────────────────────────────────────────────────┐
                  │              State Street Inbound Channels             │
                  │   Voice Telephony (DID)       Investor Portal (Web)    │
                  └───────────┬────────────────────────────┬───────────────┘
                              │ SIP Trunk                  │ HTTPS / WSS
                              ▼                            ▼
                  ┌───────────────────────┐    ┌───────────────────────────┐
                  │ Google Telephony Edge │    │  CES Web Chat Messenger   │
                  │ (GTP / Iridessa B2BUA)│    │  (Web Component / SDK)    │
                  └───────────┬───────────┘    └───────────┬───────────────┘
                              │                            │
                              └─────────────┬──────────────┘
                                            ▼
                  ┌────────────────────────────────────────────────────────┐
                  │        CX Agent Studio (CXAS) Unified Runtime          │
                  │  - Intent Classification & Entity Extraction           │
                  │  - Deterministic Business Rules & Transition Routes    │
                  │  - Agentic Discovery SOPs (2-Clue Privacy Gate)        │
                  │  - Session Management & Strict Account Partitioning    │
                  └─────────────────────────┬──────────────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
        ┌─────────────────────────┐                   ┌─────────────────────────┐
        │  Cloud Run Middleware   │                   │ Live Escalation (CCaaS) │
        │  - Python Tool Backend  │                   │ - SIP REFER / UUI Header│
        │  - ZILO Works REST APIs │                   │ - Genesys Cloud / Cisco │
        │  - Zilo Work Queue CRUD │                   │ - Agent Assist Context  │
        └─────────────────────────┘                   └─────────────────────────┘
```

---

### 1. Omnichannel Routing [Priority: HIGH]

#### 1.1 Scope & Meaning in State Street Context
In State Street Institutional Transfer Agency operations, unitholders, asset managers, and custodians contact the servicing center across disparate touchpoints—primarily inbound telephone hotlines and digital investor self-service portals. Omnichannel routing ensures that:
- Interactions across Voice and Web Chat execute the exact same institutional business logic, access identical client master and transaction records, and enforce identical compliance rules.
- When an inquiry escalates from virtual self-service to a human specialist (e.g., Cash Management for missing wires or Dealing Operations for NIGO discrepancies), session context, authenticated identity, and transactional telemetry transfer without forcing the institutional client to repeat information.
- A caller transitioning from chat to voice maintains conversational continuity.

#### 1.2 Google Cloud / GECX Solution Architecture
- **Unified Conversational Agent Engine:** A single CXAS conversational agent deployed across both the Google Telephony Platform (GTP) voice runtime and the CES Chat Messenger web widget runtime. Voice and Chat represent delivery channels, not distinct agents.
- **Voice Gateway Architecture:** Carrier SIP trunk terminates on Google Telephony Platform (`us.telephony.goog` / `sip.voice.telephony.goog`). GTP acts as a Back-to-Back User Agent (B2BUA) handling low-latency Speech-to-Text (STT) and Text-to-Speech (TTS) streaming.
- **Live Agent Handoff Signaling:** Escalations execute via `LIVE_AGENT_HANDOFF` fulfillment. For voice, GTP issues a `SIP REFER` (or SIP re-INVITE depending on SBC configuration) to the enterprise Session Border Controller (AudioCodes Mediant / Cisco CUBE), populating standard **SIP User-to-User Information (UUI)** headers and custom `x-headers`:
  ```text
  User-to-User: StateStreet-TA;SessionId=723f5306;Account=ACC-1001;CUJ=Settlement;Queue=CashMgmt;Encoding=hex
  x-gecx-session-id: 723f5306-ad25-44ab-a821-eeb2d58e18d3
  x-account-no: ACC-1001
  x-escalation-reason: SUBNR_SD_PLUS_1_OVERDUE
  ```
- **CCaaS Ingestion:** The enterprise CCaaS platform (Genesys Cloud CX, Cisco Unified Contact Center Enterprise, or Salesforce Service Cloud MIAW) parses the UUI header to place the call into the appropriate skill queue and populates the human agent desktop.

#### 1.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (OOTB CXAS channel configuration + Custom CCaaS SBC/SIP header mapping). Complexity: **Medium-High**.
- **Step-by-Step Technical Realization:**
  1. *CXAS Agent Definition:* Configure a single agent with dual channel targets (Voice and Text). Declare all inbound session variables (`telephony_caller_id`, `user_id`, `channel_type`) in the CXAS Variables tab.
  2. *SIP Trunk Binding:* In GCP Console (`Telephony -> Integrations`), bind the State Street DID to the Conversation Profile referencing the CXAS agent.
  3. *Escalation Route Configuration:* On escalation transition nodes, define `LiveAgentHandoffPayload` with structured JSON containing `account_no`, `trade_ref`, `escalation_reason`, and `target_skill_group`.
  4. *SBC Normalization:* Configure AudioCodes / Cisco CUBE SIP normalization rules to map `LiveAgentHandoffPayload` fields into outbound `User-to-User` and `X-` SIP headers toward Genesys Cloud CX.

#### 1.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Demonstrate voice and chat functional parity using identical agent logic and tools. Voice delivered via Google Telephony Platform test DID; chat delivered via embedded web widget. Escalation demonstrated by emitting structured context payloads and auto-generating human agent summaries.
- **Production Rollout:** Direct carrier SIP trunk peering (GTP inter-cloud peering with Genesys Cloud EX or dedicated TLS SBC trunks), cross-channel state synchronization using Cloud Spanner / Memorystore for Redis, and bidirectional omnichannel switching.

---

### 2. Omni Channel Outbound Campaigns [Priority: LOW]

#### 2.1 Scope & Meaning in State Street Context
Institutional transfer agency operations require proactive, time-sensitive client outreach to prevent operational settlement failures:
- **SUBNR Debtor Outreach:** Alerting asset managers before daily banking cut-offs (e.g., 12:00 GMT / 4:00 PM EST) that subscription funds have not arrived for a pending deal ticket.
- **NIGO Discrepancy Alerts:** Notifying authorized traders that a trade instruction was placed in the Not In Good Order (`NIGO`) queue due to missing signatures, incorrect settlement currency, or mismatched ISINs.
- **Valuation Point / Cut-off Reminders:** Notifying institutional investors of early bank holiday dealing cut-offs.

#### 2.2 Google Cloud / GECX Solution Architecture
- **Event-Driven Trigger Architecture:** ZILO Work item updates or Bank Reconciliation unmatched events emit webhooks into GCP Eventarc / Cloud Pub/Sub.
- **Campaign Orchestrator (Cloud Run):** A containerized campaign orchestration service filters events, verifies investor contact preferences/operating hours, and schedules outreach tasks in Cloud Tasks.
- **Dialer & Messaging Dispatcher:**
  - *Outbound Telephony:* The orchestrator initiates outbound calls via the CCaaS native campaign dialer (Genesys Outbound / Cisco Outbound Option) or Google Cloud Conversational Telephony Outbound API.
  - *Outbound Digital:* Dispatches transactional SMS (via Twilio/Sinch) or secure portal notification containing a deep link to resume the session in the web chat widget.
- **Conversational Context Pre-loading:** When the outbound call connects, GTP routes the call into CXAS with pre-populated session parameters (`$session.params.campaign_type = "NIGO_ALERT"`, `$session.params.trade_ref = "TRD-5004"`), enabling Tara to immediately deliver the context-aware alert.

#### 2.3 Implementation Strategy & Complexity
- **Classification:** Custom Integration. Complexity: **High** (requires dialer integration, pacing algorithms, and regulatory compliance).
- **Step-by-Step Technical Realization:**
  1. Create a Cloud Pub/Sub topic `ta-outbound-events` subscribed to Zilo Work webhook notifications.
  2. Implement a Cloud Run microservice that aggregates events, dedupes against open customer tickets, and validates TCPA / regulatory calling hours.
  3. Invoke CCaaS Outbound Campaign REST APIs or initiate outbound sessions using the CXAS Telephony Outbound API.
  4. Pass contextual metadata into the session start parameters to trigger the outbound notification flow.

#### 2.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Formally deferred per Mark Healy’s sign-off. Architectural design and event schemas documented in project blueprint; no live outbound dialer demonstrated.
- **Production Rollout:** Phase 2/3 delivery. Implement automated SUBNR cash-chase outbound campaigns integrated directly with Zilo Work item events and daily bank reconciliation exceptions.

---

### 3. Skills and Proficiency Routing [Priority: MEDIUM]

#### 3.1 Scope & Meaning in State Street Context
Institutional Transfer Agency operations are highly specialized. Inquiries cannot be escalated to a generic pool of customer service representatives:
- **Cash Management Desk:** Dedicated specialists handling complex SWIFT MT103/MT202 wire matching, bank account reconciliation, and SUBNR overdue exceptions.
- **Dealing Operations Desk:** Specialists authorized to remediate trade discrepancies, review NIGO queues, re-index documents in DINDEX, and execute cancellations/re-bookings.
- **Institutional Client Service Managers (CSMs):** Tier-1 relationship managers dedicated to high-AUM institutional accounts.
Routing must evaluate account tier, transaction urgency, and operational exception type to select the appropriately skilled agent.

#### 3.2 Google Cloud / GECX Solution Architecture
- **CXAS Parameter Evaluation:** CXAS dynamically assesses conversation attributes:
  - `$session.params.cuj_name`: `DealTickets` vs. `ReceiptOfMonies`.
  - `$session.params.exception_type`: `NIGO_QUEUE`, `SUBNR_SD_PLUS_1`, `AUTH_FAILURE`.
  - `$session.params.investor_tier`: `Tier_1_Institutional` vs. `Standard`.
- **Target Skill Mapping Logic:** CXAS maps these parameters into specific CCaaS routing attributes:
  ```json
  {
    "route_target": "HUMAN_AGENT",
    "primary_skill": "TA_CASH_MANAGEMENT",
    "proficiency_level": 5,
    "fallback_skill": "TA_DEALING_OPERATIONS",
    "priority": "HIGH",
    "context": {
      "account_no": "ACC-1022",
      "trade_ref": "TRD-5012",
      "exception": "SUBNR_SD_PLUS_1"
    }
  }
  ```
- **Handoff Mechanism:** Encoded into the SIP `User-to-User` header or forwarded via CCaaS REST Handoff API to trigger Genesys Cloud ACD Bullseye Routing or Cisco Precision Routing.

#### 3.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (CXAS conditional routing + CCaaS ACD queue configuration). Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. In CXAS, create conditional route groups on exception states.
  2. Define specific handoff targets based on transaction attributes:
     - If `$session.params.subnr_flag == "Yes"` and `$session.params.is_sd_plus_1 == true` -> Set `target_queue = "TA_Cash_Management"`.
     - If `$session.params.trade_status == "NIGO"` -> Set `target_queue = "TA_Dealing_Operations"`.
     - If `$session.params.auth_attempts >= 3` -> Set `target_queue = "TA_Identity_Verification"`.
  3. Configure the CCaaS gateway to read the metadata payload and route to the corresponding ACD skill group.

#### 3.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** CXAS demonstrates dynamic skill determination across all 7 demo scenarios. When an escalation trigger fires (e.g., CUJ2-D NIGO or CUJ3-C SUBNR SD+1), the agent explicitly identifies the target team ("Cash Management" or "Dealing Operations") in the dialogue and emits structured metadata payload.
- **Production Rollout:** End-to-end integration with Genesys Cloud / Cisco CTI routing queues, real-time agent presence awareness, and dynamic SLA-based queue overflow.

---

### 4. Task Management [Priority: HIGH]

#### 4.1 Scope & Meaning in State Street Context
In transfer agency operations, complex exceptions frequently require asynchronous human work that cannot be completed while the caller is on the line. When an institutional investor calls about a missing wire or a trade stalled in the dealing queue:
- The system must query active workflow items from **Zilo Work** (and legacy **AWD** queues: `DEALING`, `DINDEX`, `NIGO`, `AUDIT`).
- The virtual agent must interpret queue status and provide clear operational updates.
- If unresolvable, the agent must create or update a work item in Zilo Work, attaching full conversational context, call transcripts, and investor-provided reference numbers.

#### 4.2 Google Cloud / GECX Solution Architecture
- **CXAS Agentic Tools:** Custom tools configured via OpenAPI specifications calling Cloud Run middleware connected to the Zilo Work REST API.
- **Core Task Management APIs:**
  - `getWorkItemStatus(trade_ref, queue_name)`: Checks current state in `DEALING`, `DINDEX`, or `NIGO`.
  - `createWorkItem(account_no, issue_type, priority, case_notes)`: Creates an asynchronous task in Zilo Work.
  - `updateWorkItemComments(work_item_id, notes)`: Appends transcription context and investor statements.
- **Asynchronous Execution & Resilience:** Cloud Tasks and Pub/Sub ensure that task generation requests are delivered to Zilo Work with guaranteed at-least-once execution, handling backend throttling or maintenance windows.

#### 4.3 Implementation Strategy & Complexity
- **Classification:** Custom Integration. Complexity: **Medium-High**.
- **Step-by-Step Technical Realization:**
  1. *Tool Definition:* Define OpenAPI schemas in CXAS for work item queries and task creation.
  2. *Middleware Bridge:* In `statestreet_tools.py` (deployed on Cloud Run), implement deterministic lookup and creation functions against the Zilo Work API / mock store.
  3. *State Transitions:* In CXAS, wire tool outputs directly into conversational logic:
     - If queue is `DINDEX` -> Inform caller the trade is indexed and undergoing dealing verification (CUJ 2-C).
     - If queue is `NIGO` -> Fetch discrepancy comment and initiate escalation with case creation (CUJ 2-D).

#### 4.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Implemented and fully validated using high-fidelity mock tools (`check_dealing_queue`, `search_zilo_work_items`). The agent successfully discriminates between `DINDEX` (in-progress) and `NIGO` (escalated exception) states and outputs structured task escalation metadata.
- **Production Rollout:** Full bi-directional REST integration with Zilo Work Items API and AWD legacy bridge, automated SLA tracking, and bi-directional status updates via Webhook.

---

### 5. Rules Engine [Priority: HIGH]

#### 5.1 Scope & Meaning in State Street Context
Transfer agency servicing is governed by rigid regulatory and operational financial rules where probabilistic LLM behavior is unacceptable. Strict deterministic logic is required for:
1. **The 2-Clue Privacy Corroboration Rule:** In Agentic Discovery, the virtual agent must never disclose candidate trades or details until the caller provides at least 2 independent corroborating attributes (e.g. approximate date + fund name + approximate amount). Single clues must fail the gate.
2. **Strict Account Partitioning:** Candidate searches must be strictly bounded to the authenticated account; closer matches on other accounts must be completely ignored.
3. **NIGO Rule:** Trades in `NIGO` status must never be confirmed as valid; the agent must read the exact discrepancy comment and escalate.
4. **SUBNR SD+1 Rule:** If a trade is Unsettled, Bank Rec is Unmatched, SUBNR is Yes, and the date is Settlement Date + 1, immediate escalation to Cash Management is mandatory.
5. **Dealing Cut-Off Rules:** Subscription instructions received after valuation cut-off (e.g. 12:00 GMT) must be explicitly identified as taking the next valuation point's NAV.

#### 5.2 Google Cloud / GECX Solution Architecture
- **Layered Multi-Tier Rules Architecture:**
  ```text
  ┌────────────────────────────────────────────────────────┐
  │ Tier 1: CXAS Flow Transition Rules & Conditions (CEL)  │
  │ - State machine routing, intent confidence gates       │
  ├────────────────────────────────────────────────────────┤
  │ Tier 2: Deterministic Prompt SOP Guardrails            │
  │ - System instructions with negative RFC-style rules    │
  ├────────────────────────────────────────────────────────┤
  │ Tier 3: Backend Python Tool Gate Enforcement           │
  │ - Programmatic corroboration gates, parameter bounds   │
  ├────────────────────────────────────────────────────────┤
  │ Tier 4: CCAI Insights CEL Autolabeling Rules           │
  │ - Post-call compliance audit and quality verification  │
  └────────────────────────────────────────────────────────┘
  ```
- **Backend Gate Enforcement:** In `statestreet_tools.py`, the 2-clue corroboration rule is implemented as a deterministic code barrier:
  ```python
  if score < 2:
      return {
          "status": "gate_failed",
          "corroboration_score": score,
          "message": "Corroboration gate failed. Fewer than 2 qualifying clues provided."
      }
  ```
  The LLM never receives candidate trade records until this code-level gate passes.

#### 5.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (CXAS flow transitions + Python microservice validation). Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. *Prompt Engineering:* Author explicit SOP rules in Tara's system prompt forbidding speculation or candidate disclosure without verified clues.
  2. *Tool Logic:* Implement programmatic validation checks in the Python tool layer before querying trade databases.
  3. *Transition Routes:* Configure CXAS flow conditional expressions to handle gate failures deterministically without model improvisation.
  4. *CCAI Autolabeling:* Deploy CEL autolabeling rules (`autolabel_rules.yaml`) in CCAI Insights to flag any conversation where privacy gates or escalation rules were breached.

#### 5.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** 100% implemented and verified across all 13 test scenarios (7 baseline + 6 agentic discovery). The 2-clue corroboration gate, strict account isolation, NIGO handling, and SUBNR SD+1 escalation execute deterministically.
- **Production Rollout:** Migration of business rules to an enterprise centralized rule engine (e.g. Drools, Google Cloud CEL engine, or ZILO native rule engine) with version-controlled audit trails and business analyst authoring UI.

---

## Section 2: Agentic & Conversational AI

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    CXAS Agentic Core Architecture ("Tara")                   │
│                                                                              │
│  ┌───────────────────────┐  Strict Auth Boundary   ┌──────────────────────┐  │
│  │ Investor Auth Flow    │═════════════════════════>│ Zilo Client Master   │  │
│  │ (Account No + MFA)    │                          │ Context Injection    │  │
│  └───────────────────────┘                          └──────────┬───────────┘  │
│                                                                │              │
│  ┌─────────────────────────────────────────────────────────────▼───────────┐  │
│  │ System Prompt SOPs & Guardrails:                                        │  │
│  │ - "Accuracy outranks friendliness"                                      │  │
│  │ - Strictly NO exclamation marks / NO emojis                             │  │
│  │ - Acknowledge frustration EXACTLY ONCE                                  │  │
│  │ - Grounded outputs only; zero financial hallucination                   │  │
│  └─────────────────────────────┬───────────────────────────────────────────┘  │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Agent Assist Integration:                                               │  │
│  │ - Real-time Turn Telemetry -> Summarization Generator (`generator.proto`)│  │
│  │ - Structured Case Notes (Account, ISIN, Trade Ref, Exception, Action)   │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### 6. Authentication-Aware Personalization [Priority: MEDIUM]

#### 6.1 Scope & Meaning in State Street Context
Institutional transfer agency accounts manage tens of millions of dollars across institutional funds (e.g., Global Horizon Fund, European Equity Fund). Servicing cannot proceed without rigorous verification:
- Callers must be verified against their registered investor profile (Account Number, authorized contact name, email, phone number, and security challenge/MFA).
- Once authenticated, the agent must greet the caller acknowledging their institution/firm name.
- Crucially, authentication establishes a **Strict Account Boundary**: all subsequent trade, balance, and settlement queries are scoped strictly to the authenticated account (`ACC-1001`), preventing any accidental disclosure of other unitholders' data.

#### 6.2 Google Cloud / GECX Solution Architecture
- **CXAS Session Variables:** Upon successful authentication in CUJ 1, CXAS populates immutable session parameters:
  ```text
  $session.params.authenticated = true
  $session.params.account_no = "ACC-1001"
  $session.params.account_name = "Global Horizon Fund Master Account"
  $session.params.investor_name = "Acme Asset Management"
  $session.params.authorized_contact = "John Doe"
  ```
- **Dynamic Context Injection:** The system instruction dynamically references these parameters to tailor the dialogue:
  *"I've verified your identity for Acme Asset Management on account ACC-1001. How can I assist you with your fund transactions today?"*
- **Programmatic Scope Binding:** Tool definitions do not allow the LLM to pass arbitrary account numbers; the tool bridge automatically injects `$session.params.account_no` into all backend API calls.

#### 6.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (CXAS session management + Enterprise IAM webhook). Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. *Authentication Flow:* Model CUJ 1 as a mandatory gate page in CXAS. No transaction intent can route out of this page until `$session.params.authenticated == true`.
  2. *Verification Tool:* Connect CXAS to the Zilo Client Master Auth API (mocked via `auth_mock_data.json` for POC) to validate caller credentials.
  3. *Failure Handling:* If verification fails after 2 attempts, trigger deterministic escalation to the Identity Verification Desk.

#### 6.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Full implementation of CUJ 1. Validates Account Number, email, and security questions against `auth_mock_data.json`. Establishes personalized context and demonstrates strict account partitioning (CUJ2-DISC-03).
- **Production Rollout:** Integration with State Street Enterprise IAM / Ping Identity / Okta, voice biometrics integration (Nuance / Google Cloud Speech Biometrics), and automated ANI phone-number pre-authentication.

---

### 7. Content Safety and Policy Guardrails [Priority: MEDIUM]

#### 7.1 Scope & Meaning in State Street Context
In regulated financial operations, conversational AI must be constrained by strict negative and positive policies:
- **Tone & Persona Constraints:** Professional, calm, concise. Strictly **no exclamation marks** and strictly **no emojis**.
- **De-escalation Protocol:** If an investor is frustrated, acknowledge it **exactly once** (*"I understand this is frustrating."*) and immediately proceed with the facts without looping or over-apologizing.
- **Financial Integrity:** Never provide investment advice, predict NAV pricing, speculate on wire clearing times, or hallucinate financial quantities. Accuracy strictly outranks friendliness.

#### 7.2 Google Cloud / GECX Solution Architecture
- **CXAS Safety Settings:** Configure Vertex AI built-in safety thresholds to block hate speech, harassment, and dangerous content at the lowest tolerance (`BLOCK_LOW_AND_ABOVE`).
- **Prompt-Level EARS/RFC Negative Constraints:** System instructions authored with explicit contractual prohibitions.
- **Google Model Armor / Vertex AI Guardrails:** Positioned as an inline inspection layer between CXAS and the underlying Gemini foundation model to sanitize prompts, detect jailbreak attempts, and suppress hallucinated financial numbers.
- **Grounded Tool Output:** The model is structurally constrained to generate responses only from data fields returned by tool executions.

#### 7.3 Implementation Strategy & Complexity
- **Classification:** OOTB Platform Features + Prompt Engineering. Complexity: **Low-Medium**.
- **Step-by-Step Technical Realization:**
  1. Set safety filters in CXAS Agent Settings.
  2. Embed persona rules in the global agent instructions (as verified in `CUJ_2` and `CUJ_3` instruction files).
  3. Author unit eval tests in CXAS Evaluation Suite to test negative constraints (e.g. attempting to solicit investment advice or prompt injections).

#### 7.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** 100% configured for "Tara". Zero emojis, zero exclamation marks, single-acknowledgment de-escalation, and strict factual adherence validated in the test suite.
- **Production Rollout:** Enterprise deployment of Google Cloud Model Armor with custom financial compliance filters, continuous automated red-teaming, and model jailbreak monitoring.

---

### 8. Conversation Summarization and Case Notes [Priority: MEDIUM]

#### 8.1 Scope & Meaning in State Street Context
When a transaction exception necessitates human intervention (e.g., SUBNR SD+1 overdue payment, NIGO dealing review, wire mismatch), the receiving human agent needs an instantaneous, high-density case summary. Forcing an institutional client to re-explain a complex multi-million dollar transaction failure creates severe operational friction and degrades NPS.

#### 8.2 Google Cloud / GECX Solution Architecture
- **Google Cloud Agent Assist Summarization:** Leverages the native Agent Assist Conversation Profile and Summarization Generator (`generator.proto`).
- **Domain-Specific Summarization Prompt:** Pre-configured with a structured prompt template optimized for transfer agency operations:
  ```json
  {
    "summary_schema": {
      "interaction_type": "Institutional Transfer Agency Inquiry",
      "account_number": "{account_no}",
      "investor_name": "{investor_name}",
      "intent": "{primary_intent}",
      "transaction_details": {
        "trade_ref": "{trade_ref}",
        "isin": "{isin}",
        "amount": "{amount}",
        "status": "{status}"
      },
      "exception_reason": "{escalation_reason}",
      "suggested_action": "{recommended_next_step}"
    }
  }
  ```
- **Agent Desktop Delivery:** Pushed via Agent Assist UI Connector into the Salesforce Service Cloud / Genesys Workspace case activity feed.

#### 8.3 Implementation Strategy & Complexity
- **Classification:** OOTB Platform Capability. Complexity: **Low-Medium**.
- **Step-by-Step Technical Realization:**
  1. In Google Cloud Console, navigate to `Agent Assist -> Generators` and create a `CONVERSATION_SUMMARIZATION` generator.
  2. Define the few-shot summarization prompt tailored to TA trade exceptions.
  3. Bind the generator to the active Conversation Profile serving the interaction.
  4. Ensure the CTI connector is listening for `GenerateConversationSummaryResponse` events upon live agent handoff.

#### 8.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Auto-generated structured case summaries demonstrated upon escalation for NIGO and SUBNR scenarios, visible in the Agent Assist demo interface and execution logs.
- **Production Rollout:** Full integration with State Street's Salesforce Service Cloud / Genesys Interaction Desktop, automatically committing case notes directly into Zilo Work item comment threads.

---

### 9. Multilingual Understanding and Generation [Priority: LOW]

#### 9.1 Scope & Meaning in State Street Context
State Street provides transfer agency services for cross-border UCITS and AIFMD funds registered in Dublin, Luxembourg, the UK, and international distribution hubs. While English is the institutional market standard for dealing desks, servicing centers often receive inquiries in French, German, Italian, Spanish, and Japanese from regional asset managers and distributors.

#### 9.2 Google Cloud / GECX Solution Architecture
- **Native CXAS Multilingual Engine:** CXAS supports multi-locale agent definitions. When enabled, the underlying Gemini LLM processes user utterances in any supported language, maps them to the canonical intent, executes tool calls with standardized parameters, and generates localized responses.
- **Speech-to-Text / Text-to-Speech Localization:** Google Cloud Telephony Platform supports regional Cloud STT and Neural2 / Studio TTS voice models across all European and Asian locales.
- **Dynamic Language Detection:** The conversational runtime detects language switches on turn 1 and automatically updates the session locale (`$session.params.language_code`).

#### 9.3 Implementation Strategy & Complexity
- **Classification:** OOTB Platform Capability. Complexity: **Low**.
- **Step-by-Step Technical Realization:**
  1. Add desired secondary languages (e.g. `fr-FR`, `de-DE`) in CXAS Agent Settings.
  2. Maintain tool definitions in standard English; Gemini automatically handles translation between user dialogue and tool inputs/outputs.
  3. Configure regional TTS voices matching State Street’s professional brand standards.

#### 9.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Scoped to English-only (`en-US` and `en-GB`) per Mark Healy’s sign-off.
- **Production Rollout:** Enable French and German locales for Luxembourg and Dublin UCITS fund servicing during Phase 2.

---

## Section 3: Analytics & Insights Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Analytics & Compliance Data Pipeline                     │
│                                                                             │
│   Inbound Voice Call ──────────────> Google Telephony Platform (GTP)        │
│                                            │                                │
│                     ┌──────────────────────┴──────────────────────┐         │
│                     │ Native Recording (`SessionAudioRecorder.cc`) │         │
│                     ▼                                             ▼         │
│         Google Cloud Storage (GCS)                     CCAI Insights        │
│         - Dual-channel Audio                           - STT Transcripts    │
│         - CMEK + Object Lock (WORM)                    - Turn Metrics       │
│         - 7-year Retention Policy                      - Sentiment Scoring  │
│                                                           │                 │
│                                                           ▼                 │
│  ┌─────────────────────────┐               ┌─────────────────────────────┐  │
│  │ Cloud DLP Masking       │<══════════════│ CEL Autolabeling Rules      │  │
│  │ - PII / PCI redaction   │               │ - Classify Subagents        │  │
│  │ - Account/Trade masking │               │ - Tag Escalation Types      │  │
│  └─────────────────────────┘               └──────────────┬──────────────┘  │
│                                                           │                 │
│                                                           ▼                 │
│                                            ┌─────────────────────────────┐  │
│                                            │ BigQuery Analytics &        │  │
│                                            │ CCAI Configurable Dashboards│  │
│                                            │ (Vega-Lite / Looker Studio) │  │
│                                            └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 10. Call Recording [Priority: HIGH]

#### 10.1 Scope & Meaning in State Street Context
SEC Rule 17a-4, FINRA Rule 4511, and MiFID II mandate complete, immutable recording of all voice communications related to trade orders, transaction confirmations, and money movement. Inquiries concerning deal tickets, wire instructions, and cash settlements are subject to strict regulatory retention (5 to 7 years) and legal discovery.

#### 10.2 Google Cloud / GECX Solution Architecture
Two validated enterprise architectures exist for recording:
- **Approach 1: Native Google Cloud Recording (OOTB GTP):**
  - Enabled via `SecuritySettings` (`security_settings.proto`) configured with an `AudioExportSettings` GCS bucket (`gs://statestreet-call-recordings`).
  - Attached directly to the Conversation Profile serving the SIP trunk.
  - Media bridge (`SessionAudioRecorder.cc`) writes dual-channel audio directly to GCS.
  - *Transfer Strategy Constraint:* If transfer to a human agent uses `sip-refer: true` (blind referral), the virtual agent session ends upon `SIP BYE`, and native recording terminates at handoff. To record the human agent leg natively, GTP must act as a B2BUA (`sip-refer: false`) with Agent Assist / CCaaS configured on the profile.
- **Approach 2: SBC-Initiated SIPREC (Recommended for Enterprise Production):**
  - The border SBC (AudioCodes Mediant / Cisco CUBE) acts as the Session Recording Client (SRC).
  - Forks real-time dual-channel RTP via `SIPREC` (RFC 7865/7866) directly to State Street’s enterprise Session Recording Server (SRS) such as Verint, NICE, or SmartTAP.
  - *Advantage:* Records the entire interaction (`Leg 1: Virtual Agent + Leg 2: Human Agent`) regardless of transfer mode, with zero Google B2BUA bridge charges during the human leg. Requires SBC Media Bypass to be explicitly disabled.

#### 10.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (GTP Security Settings for Native; SBC configuration for SIPREC). Complexity: **Medium**.
- **Step-by-Step Technical Realization (Native Approach):**
  1. Create GCS bucket `gs://ss-ta-poc-call-recordings` with Customer Managed Encryption Keys (CMEK).
  2. Create CXAS Security Settings profile specifying the GCS bucket path.
  3. Link Security Settings to the Conversation Profile (`ContactCenterRuntimeModule::GetSecuritySettingsName()`).
  4. Verify dual-channel `.wav` files are successfully written post-interaction.

#### 10.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Native Google Cloud Recording enabled via GTP Security Settings to Cloud Storage, capturing all demo interactions for verification.
- **Production Rollout:** SBC-Initiated SIPREC forking to State Street Verint/NICE compliance clusters with secondary GCS archive configured with Cloud Storage Object Retention (Bucket Lock / WORM) for SEC 17a-4 compliance.

---

### 11. Data Redaction [Priority: LOW]

#### 11.1 Scope & Meaning in State Street Context
While institutional fund administration does not routinely handle consumer credit cards, calls frequently transmit sensitive banking and personal information: SWIFT BICs, IBANs, bank routing numbers, authorized signatory phone numbers, and email addresses. To prevent data leakage into operational logs and analytics platforms, sensitive data must be redacted from transcripts and audio files.

#### 11.2 Google Cloud / GECX Solution Architecture
- **Cloud Sensitive Data Protection (Cloud DLP / DLP v2 API):** Integrated natively into CXAS Security Settings and CCAI Insights.
- **De-identification Templates:** Configured with infoTypes:
  - Built-in: `EMAIL_ADDRESS`, `PHONE_NUMBER`, `IBAN_CODE`, `SWIFT_CODE`, `US_BANK_ROUTING_MICR`.
  - Custom regex: `STATE_STREET_ACCOUNT_NO` (`ACC-\d{4}`), `STATE_STREET_TRADE_REF` (`TRD-\d{4}`).
- **Dual Redaction:**
  - *Text Transcripts:* Sensitive tokens replaced with masking surrogates (e.g. `[REDACTED_IBAN]`).
  - *Audio Redaction:* Audio segments corresponding to sensitive numeric tokens muted or masked.

#### 11.3 Implementation Strategy & Complexity
- **Classification:** OOTB Platform Feature. Complexity: **Low-Medium**.
- **Step-by-Step Technical Realization:**
  1. Author Cloud DLP DeidentifyTemplate in GCP project.
  2. Reference the template ID in the CXAS `SecuritySettings.redaction_profile`.
  3. Enable transcript redaction in CCAI Insights Project Settings.

#### 11.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Scoped as Low priority per Mark Healy’s sign-off. Basic regex masking configured in CXAS Security Settings; candidate trade reference masking demonstrated in tool logic (`***5102`).
- **Production Rollout:** Enterprise Cloud DLP inspection and crypto-tokenization pipeline across all ingested CCAI Insights transcripts and GCS recordings.

---

### 12. Real-Time and Historical Analytics [Priority: HIGH]

#### 12.1 Scope & Meaning in State Street Context
Operations executives require full operational observability into contact center performance:
- Tracking inquiry distribution across trade confirmation (Deal Tickets) and cash settlement (Receipt of Monies).
- Measuring First-Contact Containment Rate (resolution without human intervention).
- Monitoring escalation spikes during critical dealing cut-off windows (e.g. 11:30 AM to 12:00 PM cut-off).
- Analyzing sentiment shifts to identify systemic operational failures (e.g., recurring wire matching delays with a specific clearing bank).

#### 12.2 Google Cloud / GECX Solution Architecture
- **CCAI Insights Telemetry Pipeline:** Ingests conversation data in real time from CXAS runtime.
- **Generative AI Insights & Topic Modeling:** Automatically clusters calls into semantic topic clusters and classifies sentiment trajectories (caller vs. agent).
- **CEL Autolabeling Rules (`autolabel_rules.yaml`):** Evaluates conversations against business rules to apply operational tags:
  ```yaml
  autolabeling_rules:
    - rule_id: "cuj_classifier"
      label_key: "ta_journey"
      conditions:
        - condition: "containsSubAgent(conversation, 'deal_tickets')"
          value: "'Deal_Tickets'"
        - condition: "containsSubAgent(conversation, 'receipt_of_monies')"
          value: "'Receipt_of_Monies'"
        - condition: ""
          value: "'General_Inquiry'"
  ```
- **BigQuery Streaming Export:** Continuous streaming of conversation metadata, turns, labels, and metrics into BigQuery for ad-hoc analysis.

#### 12.3 Implementation Strategy & Complexity
- **Classification:** OOTB Platform Capability. Complexity: **Low-Medium**.
- **Step-by-Step Technical Realization:**
  1. Provision CCAI Insights project in `us-central1`.
  2. Enable automated ingestion on the CXAS Conversation Profile.
  3. Deploy declarative autolabeling rules using `cxas insights diff-autolabel-rules` and `apply-autolabel-rules`.
  4. Configure BigQuery streaming export sink.

#### 12.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Active CCAI Insights project receiving POC test runs, demonstrating automatic topic classification, sentiment scoring, and turn-by-turn analysis.
- **Production Rollout:** Enterprise BigQuery analytics warehouse, automated anomaly detection alerts (e.g. escalation rate > 15%), and integration with State Street Enterprise Data Lake.

---

### 13. Dashboards [Priority: HIGH]

#### 13.1 Scope & Meaning in State Street Context
Executive sponsors (Sriram Piratla, Mark Healy) require an intuitive, real-time dashboard view to assess the business value and ROI of the conversational AI solution:
- High-level KPIs: Total interactions, First-Contact Containment %, Escalation %, Average Handle Time (AHT).
- Journey drill-downs: Deal Ticket statuses (`Processed`, `Pending`, `DINDEX`, `NIGO`) and Settlement outcomes (`Matched`, `Unmatched`, `SUBNR SD+1`).
- Agentic Discovery effectiveness: Proportion of missing-reference queries successfully resolved via 2-clue corroboration vs. failed gates.

#### 13.2 Google Cloud / GECX Solution Architecture
- **CCAI Insights Configurable Dashboards (`dashboards.yaml`):** Native multi-tab dashboards configured directly within the CCAI Insights console:
  - Tab 1: **Executive KPIs** (Scorecard widgets for Total Volume, Containment Rate, AHT, Escalation Rate).
  - Tab 2: **Journey Performance** (Bar and pie charts for Deal Tickets vs. Receipt of Monies).
  - Tab 3: **Exception Analysis** (Tables tracking NIGO and SUBNR escalations).
- **Visualization Spec:** Powered by Vega-Lite specs and SQL queries executing against BigQuery conversation views.
- **Looker / Looker Studio:** Complementary executive dashboard providing branded, exportable reports for steering committee presentations.

#### 13.3 Implementation Strategy & Complexity
- **Classification:** OOTB CCAI Insights Feature + Looker Studio. Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. Author `dashboards.yaml` declaring root container, tab containers, and Vega-Lite chart specifications.
  2. Deploy configuration via `cxas insights sync-dashboards --file dashboards.yaml`.
  3. Connect Looker Studio to the BigQuery export dataset to build executive slide-ready visuals.

#### 13.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Deliverable TO8045-24: Configured Executive KPI Dashboard in CCAI Insights / Looker Studio displaying real-time metrics for all POC test scenarios.
- **Production Rollout:** Enterprise Looker deployment with role-based access control (RBAC), multi-tenant fund reporting, and scheduled daily executive email digests.

---

## Section 4: Responsible AI, Privacy & Compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Enterprise Governance & Trust Perimeter                  │
│                                                                             │
│   VPC Service Controls (VPC-SC) Perimeter Boundary                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Regional Resource Pinning (US / EU Data Residency)                   │  │
│  │                                                                       │  │
│  │  ┌────────────────────────┐             ┌──────────────────────────┐  │  │
│  │  │ CXAS / Telephony Edge  │             │ Cloud Storage & BigQuery │  │  │
│  │  │ - Session Partitioning │             │ - CMEK Encryption        │  │  │
│  │  │ - Grounded Guardrails  │             │ - WORM Object Lock       │  │  │
│  │  └───────────┬────────────┘             └─────────────▲────────────┘  │  │
│  │              │                                        │               │  │
│  │              ▼                                        │               │  │
│  │  ┌────────────────────────┐             ┌─────────────┴────────────┐  │  │
│  │  │ Cloud DLP Pipeline     │════════════>│ Cloud Audit Logs         │  │  │
│  │  │ - Candidate Masking    │             │ - Non-repudiation audit  │  │  │
│  │  │ - PII/PCI Redaction    │             │ - SIEM Integration       │  │  │
│  │  └────────────────────────┘             └──────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 14. Regulatory Compliance in Local Markets [Priority: MEDIUM]

#### 14.1 Scope & Meaning in State Street Context
State Street’s institutional transfer agency business operates under stringent global financial regulations:
- **US Operations:** SEC Rule 17a-4, FINRA Rule 4511, OCC guidance on third-party risk and AI model risk management (SR 11-7).
- **European Operations (UCITS / AIFMD):** Central Bank of Ireland, CSSF (Luxembourg), FCA (UK), and the EU **Digital Operational Resilience Act (DORA)** governing ICT third-party risk.
- **Key Mandates:** Strict data residency, operational resiliency with zero single-points-of-failure, comprehensive audit trails, and deterministic AI boundaries.

#### 14.2 Google Cloud / GECX Solution Architecture
- **Data Residency & Resource Pinning:** CXAS, GTP, CCAI Insights, Vertex AI, and Cloud Storage resources are pinned to designated geographic regions (e.g. `us-central1` for US; `europe-west1` / `europe-west3` for Dublin/Luxembourg funds).
- **Compliance Certifications:** Google Cloud infrastructure meets SOC 1/2/3, ISO/IEC 27001, 27017, 27018, and PCI-DSS requirements.
- **VPC Service Controls (VPC-SC):** Establishes an encrypted security perimeter around GECX, BigQuery, and Cloud Storage, preventing unauthorized multi-tenant data exfiltration.
- **Customer Managed Encryption Keys (CMEK):** Cryptographic keys managed in Cloud KMS, allowing State Street to control data encryption and revoke access instantly.

#### 14.3 Implementation Strategy & Complexity
- **Classification:** Cloud Infrastructure Governance. Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. Provision GCP projects within State Street’s organization resource hierarchy under designated compliance folders.
  2. Enforce organization policies: `gcp.resourceLocations` restricted to allowed regions.
  3. Attach CMEK keys to Cloud Storage buckets and BigQuery datasets.
  4. Enforce VPC-SC perimeter around GECX and API endpoints.

#### 14.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Deployed in Google Cloud US region (`us-central1`), operating under standard Google security baselines with an architectural blueprint detailing DORA and UCITS compliance.
- **Production Rollout:** Multi-region deployment with dedicated European data residency for Dublin/Luxembourg operations, full VPC-SC enforcement, and formal third-party ICT DORA compliance audit.

---

### 15. Data Classification and Handling [Priority: MEDIUM]

#### 15.1 Scope & Meaning in State Street Context
State Street classifies data under strict corporate security policies: Public, Internal, Confidential, and **Limited Access** (as seen in official email headers: *"Information Classification: Limited Access"*). Unitholder trade histories, cash settlement records, and investor account numbers are Limited Access. Cross-account data pollution is an immediate regulatory violation.

#### 15.2 Google Cloud / GECX Solution Architecture
- **Strict Account Partitioning:** Built into the core architecture of CXAS tools. When `search_account`, `search_zilo_trades`, or `search_bank_reconciliation` execute, the session parameter `$session.params.account_no` is strictly enforced as a mandatory query filter.
- **Cross-Account Exclusion Validation:** Demonstrated in test scenario `CUJ2-DISC-03`, where a candidate trade matching all query criteria on account `ACC-1024` is strictly excluded because the authenticated caller is `ACC-1001`.
- **Google Cloud Dataplex & Data Catalog:** Enforces automated metadata classification, tagging sensitive data columns in BigQuery with `Classification: Limited_Access`.
- **Ephemeral Session Lifetimes:** CXAS session parameter lifetimes configured to expire upon session termination (`TTL: 20 minutes`).

#### 15.3 Implementation Strategy & Complexity
- **Classification:** Architectural Design Pattern + IAM. Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. In `statestreet_tools.py`, enforce programmatic account checks:
     ```python
     if trade["Account No"] != authenticated_account_no:
         continue  # Strictly isolate cross-account data
     ```
  2. Apply IAM least-privilege roles to service accounts invoking tools.
  3. Define Dataplex policy tags for BigQuery audit exports.

#### 15.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** 100% verified. Strict account partitioning implemented in all Python tools and proven in test case `CUJ2-DISC-03`.
- **Production Rollout:** Integration with State Street Enterprise Data Governance platforms (Collibra / Purview), automated Dataplex policy enforcement, and column-level access controls.

---

### 16. PII / PCI Detection and Masking [Priority: MEDIUM]

#### 16.1 Scope & Meaning in State Street Context
Institutional investors require protection against unauthorized exposure of account numbers, signatory contact details, and banking coordinates. In addition, the **2-Clue Privacy Corroboration SOP** dictates that candidate trade references must be masked (e.g. `***5102`) and financial amounts/unit counts withheld until the investor independently confirms the transaction.

#### 16.2 Google Cloud / GECX Solution Architecture
- **Algorithmic Candidate Masking:** Implemented directly in tool responses for Agentic Discovery. When candidate trades pass the 2-clue corroboration gate, the tool returns masked trade IDs (`***5102`), fund names, and dates, while suppressing exact cash amounts and unit counts.
- **Cloud Sensitive Data Protection (DLP):** Applied to conversational telemetry streams. Ingestion pipelines scan for SSNs, phone numbers, email addresses, and bank accounts, replacing them with cryptographic tokens or redaction strings.

#### 16.3 Implementation Strategy & Complexity
- **Classification:** Hybrid (Python Tool Logic + Cloud DLP). Complexity: **Medium**.
- **Step-by-Step Technical Realization:**
  1. *Tool Masking Logic:* In `statestreet_tools.py`, implement candidate masking logic:
     ```python
     masked_id = "***" + str(trade["Trade Ref"])[-4:]
     candidate = {
         "masked_trade_ref": masked_id,
         "fund_name": trade["Fund Name"],
         "trade_date": trade["Trade Date"],
         # amount and units explicitly withheld
     }
     ```
  2. *Cloud DLP Templates:* Create DLP inspection templates to scrub PII from logs and agent evaluation transcripts.

#### 16.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Masked candidate presentation (`***5102`) fully operational and verified in Agentic Discovery test scenarios (`CUJ2-DISC-02`, `CUJ3-DISC-02`).
- **Production Rollout:** Comprehensive Cloud DLP pipeline with reversible pseudonymization / tokenization for authorized fraud investigation.

---

### 17. Privacy Notice and Customer Consent [Priority: LOW]

#### 17.1 Scope & Meaning in State Street Context
Legal compliance across multiple jurisdictions (GDPR Article 13, California CCPA, and two-party call recording consent laws in US states like Massachusetts and California) requires informing callers that they are interacting with an AI assistant and that the call is recorded.

#### 17.2 Google Cloud / GECX Solution Architecture
- **Deterministic Greeting Fulfillment:** Modeled in the CXAS Default Welcome Flow. Before any transactional intent is classified or entity extracted, the agent states:
  *"Welcome to State Street Investor Services. I am Tara, an AI conversational assistant. Please be advised that this call is recorded and monitored for compliance and servicing purposes."*
- **Consent Refusal Route:** If a caller explicitly states *"I do not consent to recording"* or *"I refuse to speak to an AI"*, CXAS follows a conditional transition route that immediately transfers the interaction to a live representative or terminates politely.

#### 17.3 Implementation Strategy & Complexity
- **Classification:** OOTB CXAS Flow Design. Complexity: **Low**.
- **Step-by-Step Technical Realization:**
  1. Embed the mandatory consent disclaimer in the start fulfillment message of the greeting flow.
  2. Add intent / route for recording refusal triggering immediate `LIVE_AGENT_HANDOFF`.

#### 17.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Standard compliance disclaimer embedded in "Tara's" greeting across Voice and Chat channels.
- **Production Rollout:** Dynamic ANI-based consent logic that adjusts the disclosure based on the caller's geographic location (e.g. single-party vs. two-party consent jurisdictions).

---

### 18. Audit Logging and Monitoring [Priority: LOW]

#### 18.1 Scope & Meaning in State Street Context
Financial institutions must maintain complete, non-repudiable audit logs of every system interaction. In the event of a trade settlement dispute or regulatory inquiry (SEC/FINRA), auditors must be able to reconstruct the exact dialogue, intent matches, confidence scores, tool inputs/outputs, and escalation timestamps.

#### 18.2 Google Cloud / GECX Solution Architecture
- **Google Cloud Audit Logs:** Automatically logs Admin Activity, System Events, and Data Access events.
- **CXAS Interaction Logging:** Every conversational turn is written to Cloud Logging, capturing:
  - Caller utterance and STT confidence.
  - Matched intent, extracted parameters, and page transition path.
  - Raw tool invocation payload and response payload.
  - Latency breakdown (STT, LLM reasoning, Tool execution, TTS).
- **Log Sinks & Long-Term Retention:** Cloud Logging Sink continuously routes interaction logs to BigQuery for analytical querying and to Cloud Storage (with Bucket Lock WORM policy) for 7-year regulatory retention.
- **Cloud Monitoring & Alerting:** Real-time dashboards and alert policies tracking 5xx webhook errors, latency breaches (> 2.5 seconds), and abnormal escalation volumes.

#### 18.3 Implementation Strategy & Complexity
- **Classification:** OOTB Google Cloud Services. Complexity: **Low**.
- **Step-by-Step Technical Realization:**
  1. Enable Cloud Logging on the CXAS agent and Telephony Gateway.
  2. Configure a Cloud Logging Sink routing `resource.type="dialogflow_project"` to BigQuery.
  3. Create Cloud Monitoring alerts for webhook error rates and latency.

#### 18.4 POC vs. Production Roadmap
- **October 5, 2026 POC:** Cloud Logging enabled; interaction logs and tool executions captured and validated in BigQuery.
- **Production Rollout:** Enterprise SIEM integration (streaming logs to State Street Splunk / Chronicle), 7-year WORM compliance retention on GCS, and automated real-time operational alerting.

---

## Technical Architecture Recommendations for Oct 5 Demo

1. **Focus on the 7 High-Priority NFRs:** 
   Prioritize flawless demonstration of the 7 features marked **HIGH** by Mark Healy:
   - *Omnichannel Routing:* Show dual-channel parity on Voice (US phone number) and Web Chat.
   - *Task Management & Rules Engine:* Highlight the deterministic 2-clue privacy corroboration gate, strict account isolation, NIGO dealing queue handling, and SUBNR SD+1 escalation to Cash Management.
   - *Call Recording:* Demonstrate native recording to Cloud Storage with immediate post-call playback capability.
   - *Real-Time Analytics & Dashboards:* Present the CCAI Insights executive dashboard showing live volume, containment %, and sentiment metrics.
2. **Reinforce "Tara" Persona & Policy Guardrails:**
   Demonstrate that the agent strictly adheres to regulated fund administration standards (factual, concise, zero emojis, zero exclamation marks, single-acknowledgment de-escalation).
3. **Showcase Contextual Live Agent Handoff:**
   When escalating NIGO or SUBNR SD+1 exceptions, show the structured case notes and summary generated by Agent Assist, proving that human specialists receive complete context without customer repetition.

---
*Report compiled and delivered by Google Cloud Conversational AI Architecture Team.*
