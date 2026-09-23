# State Street Transfer Agency AI Contact Center (GECX)
## Comprehensive Workflow Architecture for Core CUJs (V4 Specification)

This document visualizes the complete conversational and systems execution flows for the three core Customer User Journeys (CUJs) in scope for the **State Street GECX POC** (targeted for demo on October 5, 2026), updated to adhere strictly to the **SS Comprehensive Agent Build Requirements V4**.

---

## 1. High-Level Master Flow: End-to-End Orchestration

The master flow shows how an inbound interaction through either Voice (Inbound Telephony) or Chat (Web Widget) transitions from **CUJ 1: Authentication** into Intent Classification, and routes to **CUJ 2: Deal Tickets** or **CUJ 3: Receipt of Monies**, with specialized routing across **6 Dedicated Escalation Queues**.

```mermaid
flowchart TD
    Start(["Inbound Customer Interaction (Voice Call or Web Chat)"]) --> Greet["Tara: 'Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?'"]
    Greet --> CUJ1["CUJ 1: Multi-Factor Authentication & Customer Profile Retrieval"]
    
    CUJ1 --> AuthCheck{"Authenticated & Profile Retrieved?"}
    AuthCheck -- "No (Lockout / Unverified)" --> EscAuth["Escalate to Dedicated Queue (Identity Verification / Security)"]
    AuthCheck -- "Yes" --> EstablishContext["Establish Customer Context in Session<br/>'Authentication successful. Welcome to State Street Treasury Advisory. How can I assist you with account ACC-XXXX today?'"]
    
    EstablishContext --> IntentCapture["Capture Investor Query & Classify Intent"]
    
    IntentCapture --> IntentSwitch{"Classified Intent"}
    IntentSwitch -- "Deal Ticket / Trade Confirmation" --> CUJ2["CUJ 2: Deal Tickets Workflow (CUJ2-A to CUJ2-E)"]
    IntentSwitch -- "Receipt of Monies / Settlement Inquiry" --> CUJ3["CUJ 3: Receipt of Monies Workflow (CUJ3-A to CUJ3-D)"]
    IntentSwitch -- "Human Request / Complaints" --> EscHuman["Escalate to Investor Services (Human)"]

    subgraph EscalationTargets ["V4 Specialized Escalation Queues"]
        Q1["Identity Verification (Unmatched contact / Lockout)"]
        Q2["Security Desk (Automated guessing / Brute force)"]
        Q3["Technical Support (OTP Service / Gateway timeout)"]
        Q4["Account Management (Suspended / Closed accounts)"]
        Q5["Cash Management (SUBNR Overdue Monies)"]
        Q6["Investor Services (Human Representative / Complaints)"]
    end
    
    CUJ1 -.-> Q1
    CUJ1 -.-> Q2
    CUJ1 -.-> Q3
    CUJ1 -.-> Q4
    CUJ3 -.-> Q5
    IntentSwitch -.-> Q6
```

---

## 2. CUJ 1: Investor Authentication & Customer Profile Flow (V4 Multi-Factor OTP)

Authentication is the mandatory entry gate. No transactional or financial information can be queried or disclosed prior to successful verification. Per V4, Chat and Voice diverge in their OTP delivery and validation mechanism.

```mermaid
flowchart TD
    StartAuth(["Start: Inbound Session"]) --> PromptCreds["Tara: 'Hi, this is State Street Treasury Advisory, thanks for reaching out — happy to help. Could you confirm your account number?'"]
    PromptCreds --> InAccount["Investor Provides Account Number (e.g., ACC-1001)"]
    
    InAccount --> LookupProfile["Query Authentication Profiles API: GetAuthProfile(Account_No)"]
    LookupProfile --> StatusCheck{"Account Status?"}
    StatusCheck -- "Suspended / Closed (CUJ1-L)" --> EscAccMgmt["CUJ1-L: Escalate to Account Management<br/>(Withhold all account data)"] --> EndAccMgmt(["Handoff to Account Management"])
    StatusCheck -- "Active" --> CheckChannel{"Channel Type"}
    
    %% CHAT OTP PATH
    subgraph ChatPath ["Chat Authentication Route (CUJ1-A, C, D, E, F, H)"]
        CheckChannel -- "Web Chat" --> PromptEmail["Tara: 'To secure your session, please enter your registered email address.'"]
        PromptEmail --> InEmail["Investor Provides Email"]
        InEmail --> MatchEmail{"Email Matches Registered Profile?"}
        MatchEmail -- "No Match (CUJ1-F)" --> RejectEmail["Generic failure response (no account enumeration).<br/>Offer retry; Escalate to Identity Verification after retries."]
        MatchEmail -- "Match" --> SendEmailOTP["Dispatch 6-Digit Single-Use OTP to Registered Email<br/>(Valid for 5 minutes, status: Pending CUJ1-E)"]
        SendEmailOTP --> EnterChatOTP["Investor Enters OTP Code in Chat"]
    end
    
    %% VOICE OTP PATH
    subgraph VoicePath ["Voice Telephony Route (CUJ1-B, G, I)"]
        CheckChannel -- "Voice Call" --> CheckANI{"Incoming Calling Number (ANI) Verified?"}
        CheckANI -- "Withheld / Unmatched (CUJ1-G)" --> EscVoiceID["CUJ1-G: Escalate to Identity Verification<br/>(No OTP sent; unable to verify calling number)"]
        CheckANI -- "Verified (Match)" --> SendVoiceSMS["Dispatch 6-Digit Single-Use OTP via SMS to Verified Mobile"]
        SendVoiceSMS --> EnterVoiceOTP["Investor Speaks or Enters DTMF OTP Code"]
    end
    
    EnterChatOTP --> ValidateOTP
    EnterVoiceOTP --> ValidateOTP
    
    ValidateOTP{"Validate OTP Against Challenge"}
    
    ValidateOTP -- "Expired (CUJ1-D)" --> PromptExpired["Inform investor OTP expired.<br/>Allow replacement OTP if below send limit."]
    ValidateOTP -- "Invalid Attempt < 3 (CUJ1-C)" --> PromptRetry["CUJ1-C: Passcode incorrect.<br/>State attempts remaining; Allow retry."]
    ValidateOTP -- "3rd Failed Attempt (CUJ1-H)" --> LockoutID["CUJ1-H: 3 Attempts Exceeded.<br/>Session Locked; Escalate to Identity Verification."]
    ValidateOTP -- "Rapid / Automated (CUJ1-I)" --> LockoutSec["CUJ1-I: Brute Force Detected.<br/>Session Locked immediately; Escalate to Security."]
    ValidateOTP -- "System Timeout (CUJ1-J)" --> EscTech["CUJ1-J: OTP Gateway Timeout.<br/>Escalate to Technical Support."]
    
    ValidateOTP -- "Valid OTP (CUJ1-A / CUJ1-B)" --> AuthSuccess["CUJ1-A / CUJ1-B: Authentication Successful!"]
    AuthSuccess --> UnlockScope["Unlock Session Context for ACC-XXXX<br/>Tara: 'Authentication successful. Welcome to State Street Treasury Advisory. How can I assist you with account ACC-XXXX today?'"]
    UnlockScope --> ProceedCUJ(["Proceed to CUJ 2 (Deal Tickets) or CUJ 3 (Receipt of Monies)"])
```

---

## 3. CUJ 2: Deal Tickets (Trade Inquiry / Confirmation) Flow

This journey handles requests regarding submitted trade instructions (subscriptions, redemptions, switches). It features **Agentic Multi-Turn Discovery** when the Trade Reference is unknown, and dual-system lookup across **ZILO Works** (trading) and **ZILO Work Items** (queues).

```mermaid
flowchart TD
    StartCUJ2(["Start CUJ 2: Deal Ticket Request"]) --> CheckRef{"Does Investor Provide Exact Trade Reference?<br/>(e.g., TRD-5001)"}
    
    %% AGENTIC DISCOVERY SUB-FLOW
    subgraph Discovery2 ["Agentic Transaction Discovery (Missing Reference)"]
        CheckRef -- "No" --> CollectClues["Tara Prompts Approved Narrowing Questions:<br/>1. Date / Period (When submitted?)<br/>2. Transaction Type (Sub / Red / Switch?)<br/>3. Fund Name / Code<br/>4. Approx Amount or Units"]
        CollectClues --> EvaluateGate{"Privacy Corroboration Gate Check:<br/>1. Strictly within authenticated account?<br/>2. At least 2 independent attributes present?<br/>3. At least 1 non-monetary clue present?"}
        
        EvaluateGate -- "FAILED (e.g., Amount only)" --> PromptMore["Refuse Candidate Presentation.<br/>Prompt: 'Could you confirm the fund or date range?'"] --> CollectClues
        EvaluateGate -- "PASSED" --> SearchCandidates["Query Candidates in ZILO Works for Authenticated Account"]
        
        SearchCandidates --> CandCount{"Matching Records Count"}
        CandCount -- "> 5 Candidates" --> AskNarrow["Tara: 'I found several trades. Could you narrow the date or fund?'"] --> CollectClues
        CandCount -- "1 to 5 Candidates" --> SafePresent["Present Privacy-Safe Masked Summaries:<br/>• Trade Date<br/>• Fund Name<br/>• Masked Ref (e.g., ***5102)<br/>(WITHHOLD exact amounts & units)"]
        
        SafePresent --> InvestorConfirms{"Investor Confirms Intended Trade?"}
        InvestorConfirms -- "No" --> CandNotFound["Explain trade cannot be confirmed; reprompt details"]
        InvestorConfirms -- "Yes" --> SetResolvedRef["Set Trade Reference = Confirmed Candidate Ref"]
    end
    
    CheckRef -- "Yes" --> DirectRef["Use Provided Trade Reference"]
    SetResolvedRef --> QueryZiloWorks
    DirectRef --> QueryZiloWorks
    
    %% SYSTEM LOOKUP IN ZILO WORKS
    subgraph ZiloWorksLookup ["Primary Lookup: ZILO Works (Trading Core)"]
        QueryZiloWorks["Call ZiloWorks.GetTradeDetails(Account_No, Trade_Ref)"] --> ZiloStatus{"Result from ZILO Works"}
        
        ZiloStatus -- "Found: Status = Processed" --> OutcomeA["CUJ2-A (Happy Path - Processed):<br/>• Confirm trade processed<br/>• Quote exact trade date, units, price, settlement date<br/>• Sign-off: 'Let us know if you need anything else.'"]
        
        ZiloStatus -- "Found: Status = Pending" --> OutcomeB["CUJ2-B (Happy Path - Pending):<br/>• Confirm trade received and pending<br/>• Advise awaiting valuation cut-off / NAV pricing<br/>• Sign-off: 'Let us know if you need anything else.'"]
        
        ZiloStatus -- "Empty Result (Not Found)" --> QueryWorkItems["Fall-through to ZILO Work Items Queue"]
        ZiloStatus -- "System Timeout / Error" --> SystemErr["Say: 'We are having trouble accessing records right now.'<br/>Escalate if persistent."]
    end

    %% QUEUE LOOKUP IN ZILO WORK ITEMS
    subgraph WorkItemsLookup ["Secondary Lookup: ZILO Work Items (Workflow Queues)"]
        QueryWorkItems --> CallWorkItemsAPI["Call ZiloWorkItems.GetWorkItem(Account_No, Trade_Ref)"]
        CallWorkItemsAPI --> QueueStatus{"Queue Name / Status"}
        
        QueueStatus -- "Queue = DINDEX" --> OutcomeC["CUJ2-C (Dealing Index Queue):<br/>• Confirm receipt of instruction document<br/>• Advise trade is awaiting initial dealing checks<br/>• Sign-off: 'We will notify you once dealing checks are complete.'"]
        
        QueueStatus -- "Queue = NIGO" --> OutcomeD["CUJ2-D (Not In Good Order):<br/>• Retrieve operational comments from NIGO record<br/>• Explain discrepancy to investor (e.g., missing signature)<br/>• Sign-off: 'Please action the above as soon as possible.'<br/>• Warm transfer to Dealing Ops Specialist via Agent Assist"]
        
        QueueStatus -- "Not Found Anywhere" --> OutcomeNotFound["Notify investor: Reference not found in records.<br/>Advise checking reference or dealing team."]
    end
```

---

## 4. CUJ 3: Receipt of Monies (Settlement Inquiry) Flow

This journey determines whether subscription monies or wire payments have been received, matched, and settled. It performs a multi-system cross-reference between **ZILO Trades** and the **Bank Reconciliation** database (including the daily **SUBNR** outstanding monies exception file).

```mermaid
flowchart TD
    StartCUJ3(["Start CUJ 3: Receipt of Monies Query"]) --> CheckSettlementRef{"Does Investor Provide Trade / Payment Ref?<br/>(e.g., TRD-5010)"}
    
    %% AGENTIC SETTLEMENT DISCOVERY
    subgraph Discovery3 ["Agentic Settlement Discovery (Missing Reference)"]
        CheckSettlementRef -- "No" --> GatherPaymentClues["Tara Prompts Approved Narrowing Questions:<br/>• Approximate date payment sent / value date?<br/>• Fund name or share class?<br/>• Approximate wire / subscription amount?"]
        GatherPaymentClues --> Gate3{"Privacy Corroboration Gate Check:<br/>• Authenticated account only?<br/>• Amount alone cannot query Bank Rec<br/>• At least 2 clues with 1 non-monetary?"}
        
        Gate3 -- "FAILED (Amount only)" --> BlockBankRec["BLOCK Bank Rec Query.<br/>Tara: 'Do you remember the fund or when the payment was sent?'"] --> GatherPaymentClues
        Gate3 -- "PASSED" --> SearchBoundedZilo["Search qualifying candidate trades in ZILO for Account"]
        
        SearchBoundedZilo --> PresentCandidatePayment["Present Privacy-Safe Summary:<br/>• Value Date<br/>• Fund Name<br/>• Masked Ref (***5110)<br/>(WITHHOLD bank details, exact amounts)"]
        
        PresentCandidatePayment --> ConfirmTradeCandidate{"Investor Confirms Intended Subscription?"}
        ConfirmTradeCandidate -- "No" --> RepromptPay["Unable to identify payment; offer specialist transfer"]
        ConfirmTradeCandidate -- "Yes" --> CheckPreSettlement{"Is Trade in 'Pending' State in ZILO?"}
        CheckPreSettlement -- "Yes (e.g., TRD-5113)" --> ExplainPreSettled["Explain trade is still pending execution;<br/>Monies not yet due for reconciliation.<br/>Do NOT query Bank Rec."]
        CheckPreSettlement -- "No (Qualifying Trade)" --> SetCUJ3Ref["Set Confirmed Trade Reference"]
    end
    
    CheckSettlementRef -- "Yes" --> SetCUJ3Ref
    
    %% RECONCILIATION & SETTLEMENT ENGINE
    subgraph SettlementEngine ["Settlement & Cash Reconciliation Engine"]
        SetCUJ3Ref --> QueryZiloTrade["Call Zilo.GetTrade(Account_No, Trade_Ref)"]
        QueryZiloTrade --> ZiloSettlementState{"ZILO Settlement State"}
        
        ZiloSettlementState -- "Status = Settled" --> QueryBankRecMatched["Query Bank Rec: Status = Matched"]
        QueryBankRecMatched --> Outcome3A["CUJ3-A (Happy Path - Settled & Matched):<br/>• Confirm monies received and trade settled<br/>• Quote exact matched amount and received value date<br/>• Sign-off: 'Let us know if you need anything else.'"]
        
        ZiloSettlementState -- "Status = Unsettled" --> QueryBankRecUnsettled["Query Bank Rec & Check SUBNR File"]
        
        QueryBankRecUnsettled --> SUBNRCheck{"SUBNR Flag & Settlement Date"}
        
        SUBNRCheck -- "Bank Rec = Unmatched & SUBNR = No (Within Cycle)" --> Outcome3B["CUJ3-B (Not Yet Due / Monitoring):<br/>• Funds not yet matched; within normal settlement cycle<br/>• Tara: 'We are monitoring the daily bank reconciliation file and will confirm receipt once funds arrive.'"]
        
        SUBNRCheck -- "Bank Rec = Unmatched & SUBNR = Yes (SD+1 Overdue)" --> Outcome3C["CUJ3-C (Overdue Settlement - Urgent Escalation):<br/>• Flagged on SUBNR as outstanding past Settlement Date + 1<br/>• Tara: 'This has been escalated to our Cash Management team. We will update you as soon as we have news.'<br/>• Immediate High-Priority Escalation to Cash Ops with auto-summary"]
        
        ZiloSettlementState -- "Trade Not Found" --> ErrNotFound["Advise investor trade record not found; verify reference"]
    end
```

---

## 5. Summary Comparison of the 3 CUJs

| Dimension | **CUJ 1: Authentication & Profile** | **CUJ 2: Deal Tickets** | **CUJ 3: Receipt of Monies** |
| :--- | :--- | :--- | :--- |
| **Primary Systems** | Authentication Service, Zilo Profile API | ZILO Works (Trading), ZILO Work Items (Queues) | ZILO Trades, Bank Reconciliation, SUBNR File |
| **Key Personas** | Tara (Agent), Investor / Representative | Tara (Agent), Dealing Operations Specialist | Tara (Agent), Cash Management Operations |
| **Core Happy Path** | Identity verified; personalized context set | **CUJ2-A:** Trade Processed in ZILO Works | **CUJ3-A:** Settled in ZILO + Matched in Bank Rec |
| **Pending / In-Flight** | Re-prompt credentials (up to 3 attempts) | **CUJ2-B:** Pending valuation / NAV cut-off | **CUJ3-B:** Unsettled + Unmatched + SUBNR No |
| **Operational Queue** | N/A | **CUJ2-C:** DINDEX queue (awaiting checks) | N/A (Handled via Bank Rec cycle) |
| **Exception Escalation** | 3 Failed attempts $\rightarrow$ Live Agent handoff | **CUJ2-D:** NIGO queue $\rightarrow$ Live Dealing transfer | **CUJ3-C:** SD+1 SUBNR Yes $\rightarrow$ Cash Mgmt escalation |
| **Agentic Discovery** | Mandatory for unauthenticated callers | Clues corroborate masked candidate (`***5102`) | Amount alone blocked; confirm trade before Bank Rec |
