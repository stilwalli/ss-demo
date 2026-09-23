# State Street AI Agent Portal & Mock Data Platform

A full-stack demonstration portal and operational console for State Street workflows, integrating with Google Cloud Customer Engagement Suite (CES) virtual specialists and Firestore.

## Features

- **Operational Data Management**: Accounts, Trades, Work Items, and Bank Reconciliation views.
- **Direct CES Virtual Specialist Integration**: Embedded live AI assistant widget with real-time tool inspection and transfer visibility.
- **Document Management**: Upload and inspect trade tickets and confirmation documents.
- **Firestore Integration**: Backed by Google Cloud Firestore database (`statestreet`).

## Quick Start

### 1. Prerequisites
Ensure Google Cloud SDK is authenticated for Application Default Credentials (ADC):
```bash
gcloud auth application-default login
```

### 2. Run the Portal
```bash
python3 server.py
```
The server will start on port `8080` (accessible at `http://localhost:8080`).

### 3. (Optional) Re-seed Baseline Firestore Data
```bash
python3 seed_firestore.py
```
Or trigger `POST /api/reset` from within the portal UI.
