# State Street Institutional Transfer Agency AI Contact Center

Unified project workspace for the State Street GECX / Customer Engagement Suite (CES) Conversational AI solution, operational FastAPI backend, and corporate web portal.

---

## 📁 Repository Structure

```text
statestreet/
├── README.md                                             # Master project overview, architecture & quickstart
├── .gitignore                                            # Client data, mock tables & credential exclusions
│
├── agent/                                                # Live CES / GECX Agent Definitions & Instructions
│   ├── chat_agent/                                       # StateStreetGECXDemo (Web & Chat Deployment)
│   │   ├── app.json                                      # Global app config, logging & model settings
│   │   ├── deployments.json                              # Active deployments (Voice_0.1, Web Channel)
│   │   ├── agents/                                       # Prompts & agent JSON specifications
│   │   │   ├── root_agent/ (agent.json + instruction.txt)
│   │   │   ├── Deal_Tickets_Agent/ (agent.json + instruction.txt)
│   │   │   └── Receipt_of_Monies_Agent/ (agent.json + instruction.txt)
│   │   └── tools/                                        # OpenAPI tool specifications
│   │       ├── agentic_discovery_deal_ticket.json
│   │       ├── escalate_interaction.json
│   │       ├── issue_otp_challenge.json
│   │       ├── search_bank_rec.json
│   │       └── validate_otp_response.json
│   ├── voice_agent/                                      # StateStreetVoiceDemo (Telephony & Audio Deployment)
│   │   ├── app.json                                      # Audio processing & telephony configs
│   │   ├── deployments.json                              # Voice Channel deployment
│   │   ├── agents/                                       # Voice-tuned system instructions
│   │   │   ├── root_agent/ (agent.json + instruction.txt)
│   │   │   ├── Deal_Tickets_Agent/ (agent.json + instruction.txt)
│   │   │   └── Receipt_of_Monies_Agent/ (agent.json + instruction.txt)
│   │   └── tools/                                        # Voice-accessible tools
│   ├── CUJ_2_Deal_Tickets_Agent_Instructions_*.md        # Authoritative Deal Tickets SOP
│   └── CUJ_3_Receipt_of_Monies_Agent_Instructions_*.md   # Authoritative Monies SOP
│
├── api/                                                  # Operational Backend Service (FastAPI)
│   ├── main.py                                           # OpenAPI tools backend called by CES agent
│   ├── requirements.txt                                  # Python dependencies (fastapi, uvicorn, firestore)
│   ├── Dockerfile                                        # Container build file for Cloud Run
│   ├── deploy_cloud_run.sh                               # One-click Cloud Run deployment script
│   ├── openapi.json                                      # Generated OpenAPI 3.0 schema
│   ├── data/                                             # Authoritative baseline mock databases
│   │   ├── auth_mock_data.json                           # Investor MFA & account authentication profiles
│   │   └── statestreet_mock_data.json                    # ZILO Trades, Work Items, Bank Rec baseline
│   └── static/                                           # Swagger assets & customer delivery package
│
├── portal/                                               # Web Operations & AI Chat Portal
│   ├── server.py                                         # Local server & live CES API proxy (Port 8080)
│   ├── seed_firestore.py                                 # Firestore baseline seeder
│   ├── db.py                                             # Firestore connector & helpers
│   ├── static/                                           # Corporate Sibos UI & embedded widgets
│   │   ├── index.html                                    # Main portal, Operations data management, Tara chat
│   │   ├── custom-widget.html                            # Standalone Google OOTB chat messenger widget
│   │   ├── sibos-2026-hero-image.jpg
│   │   ├── solutions-designed-around-you.jpg
│   │   ├── wealth-image-hero.jpg
│   │   └── state-street-logo.svg
│   └── uploads/                                          # Document attachment storage for chat
│
└── docs/                                                 # Authoritative Docs, Evals & Test Guides
    ├── State_Street_Comprehensive_Test_Transcripts_V23.md # 22 live platform evaluation transcripts
    ├── State_Street_Chat_Transcripts_Test_Guide.md       # Turn-by-turn manual QA testing guide
    ├── State_Street_Voice_Demo_Test_Transcripts.md       # Voice demo testing transcripts
    ├── State_Street_GECX_Evaluation_Suite.md             # Golden simulation evaluation suite
    ├── State_Street_GECX_POC_Findings_Report.md          # Architectural findings & gap analysis
    ├── State_Street_TA_AI_Contact_Center_NFR_Architectural_Report.md
    ├── Recommended_Top_Customer_Journeys_POC_Updated_09.14.2026.docx
    ├── AI_Contact_Center_Plan.xlsx
    ├── Stakeholders_list_and_Matrix.xlsx
    └── all_messages.json
```

---

## 🚀 Key URLs & Environments

| Component | Target URL | Description |
| :--- | :--- | :--- |
| **Local Portal** | `http://tilwalli.c.googlers.com:8080/` | Main portal with centered Sibos corporate layout, Firestore operations table, and Tara chat widget |
| **OOTB Chat Widget** | `http://tilwalli.c.googlers.com:8080/custom-widget.html` | Standalone Google Chat Messenger integration with token broker |
| **Cloud Run Portal** | `https://statestreet-portal-api-375460843715.us-central1.run.app/` | Deployed portal environment |
| **OpenAPI Docs** | `https://statestreet-portal-api-375460843715.us-central1.run.app/docs` | Swagger interactive OpenAPI tool documentation |
| **GCS Artifacts** | `gs://tademo01/StateStreet_GECX_Customer_Delivery.zip` | Complete customer deliverable package in Cloud Storage |

---

## 🤖 Deployed CES Applications

1. **Chat Agent: `StateStreetGECXDemo`**
   - **Resource ID**: `projects/375460843715/locations/us/apps/954f9664-9865-4fdc-9ced-751589097442`
   - **Active Deployment**: `56962e42-84e1-4aa2-8932-a15ad9ea4e75` (`Voice_0.1`)
   - **Model**: `gemini-3.1-flash-live`
   - **Features**: Multi-agent routing (Root triage, MFA Email OTP, Deal Tickets, Receipt of Monies, and Escalation Dossiers).

2. **Voice Agent: `StateStreetVoiceDemo`**
   - **Resource ID**: `projects/375460843715/locations/us/apps/db6b068d-3cc1-4fcb-82be-1d3b059db67e`
   - **Active Deployment**: `Voice Channel`
   - **Features**: Telephony-optimized voice brevity, hold music during tool calls, concise settlement summaries.

---

## 🛠️ Quickstart Commands

### 1. Running the Portal Locally
```bash
cd /usr/local/google/home/stilwalli/mywork/statestreet/portal
python3 server.py
```
*Accessible on port 8080: `http://localhost:8080` or `http://tilwalli.c.googlers.com:8080/`*

### 2. Seeding or Resetting the Firestore Baseline
```bash
cd /usr/local/google/home/stilwalli/mywork/statestreet/portal
python3 seed_firestore.py
```
*Populates 4 collections (`accounts`, `trades`, `work_items`, `bank_rec`) in the `statestreet` Firestore database.*

### 3. Running the FastAPI Backend Locally
```bash
cd /usr/local/google/home/stilwalli/mywork/statestreet/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Deploying to Google Cloud Run
```bash
# Deploy Portal
cd /usr/local/google/home/stilwalli/mywork/statestreet/portal
gcloud run deploy statestreet-portal \
    --source . \
    --project gcex-contact-center-508117 \
    --region us-central1 \
    --allow-unauthenticated

# Deploy API Tools Backend
cd /usr/local/google/home/stilwalli/mywork/statestreet/api
gcloud run deploy statestreet-api \
    --source . \
    --project gcex-contact-center-508117 \
    --region us-central1 \
    --allow-unauthenticated
```

---

## 🧪 Developer Trace & Testing

### How to use Developer Trace in the Portal:
1. Open **[http://tilwalli.c.googlers.com:8080/](http://tilwalli.c.googlers.com:8080/)**.
2. Open the floating chat widget (Tara) in the bottom right corner.
3. Toggle the **Trace** switch to **ON** in the chat header.
4. Input test credentials and trade inquiries:
   - `My account number is ACC-1001`
   - `My code is 123456`
   - `Can you check status of trade TRD-5001?`
5. Observe live amber **⚡ OpenAPI Tool Request** and green **📥 OpenAPI Tool Response** telemetry cards rendering directly inline with the conversation.
