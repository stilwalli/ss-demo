#!/usr/bin/env python3
"""State Street Mock Data Portal - Backend Server connecting to Firestore 'statestreet' database."""

import base64
import http.server
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
from pathlib import Path

PORT = 8080
PROJECT_ID = "gcex-contact-center-508117"
DATABASE_ID = "statestreet"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DATABASE_ID}/documents"
STATIC_DIR = Path(__file__).parent / "static"
UPLOAD_DIR = Path(__file__).parent / "uploads"

# Google Cloud CES App & Deployment Configuration
CES_PROJECT = "375460843715"
CES_LOCATION = "us"
CES_APP_ID = "954f9664-9865-4fdc-9ced-751589097442"
CES_DEPLOYMENT_ID = "56962e42-84e1-4aa2-8932-a15ad9ea4e75"
CES_APP = f"projects/{CES_PROJECT}/locations/{CES_LOCATION}/apps/{CES_APP_ID}"
CES_DEPLOYMENT = f"{CES_APP}/deployments/{CES_DEPLOYMENT_ID}"

_token_cache = {"token": None, "expiry": 0}

def get_token():
    import time
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expiry"]:
        return _token_cache["token"]
    try:
        tok = subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            text=True
        ).strip()
        _token_cache["token"] = tok
        _token_cache["expiry"] = now + 3000
        return tok
    except Exception as e:
        print(f"Error getting access token: {e}")
        return ""

def from_firestore_field(field_obj):
    if "stringValue" in field_obj:
        return field_obj["stringValue"]
    if "doubleValue" in field_obj:
        return float(field_obj["doubleValue"])
    if "integerValue" in field_obj:
        return int(field_obj["integerValue"])
    if "booleanValue" in field_obj:
        return field_obj["booleanValue"]
    if "nullValue" in field_obj:
        return None
    if "arrayValue" in field_obj:
        return [from_firestore_field(v) for v in field_obj["arrayValue"].get("values", [])]
    if "mapValue" in field_obj:
        return {k: from_firestore_field(v) for k, v in field_obj["mapValue"].get("fields", {}).items()}
    return None

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

def firestore_list_documents(collection):
    token = get_token()
    url = f"{BASE_URL}/{collection}?pageSize=300"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = []
            for doc in data.get("documents", []):
                fields = doc.get("fields", {})
                item = {k: from_firestore_field(v) for k, v in fields.items()}
                docs.append(item)
            return docs
    except Exception as e:
        print(f"Error listing {collection}: {e}")
        return []

def firestore_upsert_document(collection, doc_id, item_dict):
    token = get_token()
    url = f"{BASE_URL}/{collection}/{doc_id}"
    fields = {k: to_firestore_value(v) for k, v in item_dict.items()}
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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def call_ces_chat(session_id, user_message):
    token = get_token()
    if not token:
        raise RuntimeError("Failed to obtain GCP access token")

    if not session_id:
        session_id = f"portal-{uuid.uuid4().hex[:12]}"

    # 1. Run session directly via CES v1 API with diagnosticInfo
    url_run = f"https://ces.googleapis.com/v1/{CES_APP}/sessions/{session_id}:runSession"
    run_req_data = json.dumps({"inputs": [{"text": user_message}]}).encode("utf-8")
    t0 = time.time()
    req_r = urllib.request.Request(
        url_run,
        data=run_req_data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_r) as resp:
        run_res = json.loads(resp.read().decode("utf-8"))

    latency_ms = int((time.time() - t0) * 1000)
    outputs = run_res.get("outputs", [])
    reply_texts = [o.get("text") for o in outputs if o.get("text")]
    reply = "\n\n".join(reply_texts) if reply_texts else "I received your inquiry. How else may I assist you?"

    tool_calls = []
    tool_responses = []
    transfer = None
    agent = "Tara (CES Virtual Specialist)"

    for o in outputs:
        # Check direct top-level keys
        if "toolCall" in o:
            tc = o["toolCall"]
            tool_calls.append({
                "tool": tc.get("displayName") or tc.get("tool", "OpenAPI Tool"),
                "args": tc.get("args", {})
            })
        if "toolResponse" in o:
            tr = o["toolResponse"]
            tool_responses.append({
                "tool": tr.get("displayName") or tr.get("tool", "OpenAPI Tool"),
                "response": tr.get("response", {})
            })
        if "action" in o:
            act = o["action"]
            if "transfer" in act:
                transfer = act.get("transfer", {}).get("target", "Specialist Agent")

        # Check diagnosticInfo messages & chunks (CES standard structure)
        diag = o.get("diagnosticInfo", {})
        for msg in diag.get("messages", []):
            role = msg.get("role", "")
            if role and role != "user":
                agent = role
            for ch in msg.get("chunks", []):
                if "agentTransfer" in ch:
                    at = ch["agentTransfer"]
                    transfer = at.get("displayName") or at.get("targetAgent", transfer)
                if "toolCall" in ch:
                    tc = ch["toolCall"]
                    tool_calls.append({
                        "tool": tc.get("displayName") or tc.get("tool", "OpenAPI Tool"),
                        "args": tc.get("args", {})
                    })
                if "toolResponse" in ch:
                    tr = ch["toolResponse"]
                    tool_responses.append({
                        "tool": tr.get("displayName") or tr.get("tool", "OpenAPI Tool"),
                        "response": tr.get("response", {})
                    })

    return {
        "reply": reply,
        "session_id": session_id,
        "agent": agent,
        "tool_calls": tool_calls,
        "tool_responses": tool_responses,
        "transfer": transfer,
        "latency_ms": latency_ms
    }

class PortalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self.handle_api_get(path)
        elif path.startswith("/uploads/"):
            file_name = os.path.basename(path)
            file_path = UPLOAD_DIR / file_name
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")
        elif path == "/" or path == "":
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self.handle_api_post(path)
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self.handle_api_put(path)
        else:
            self.send_error(404)

    def handle_api_get(self, path):
        try:
            if path == "/api/accounts":
                docs = firestore_list_documents("accounts")
                # Sort by account_no
                docs.sort(key=lambda x: str(x.get("account_no", "")))
                self.respond_json(docs)
            elif path == "/api/trades":
                docs = firestore_list_documents("trades")
                docs.sort(key=lambda x: str(x.get("trade_ref", "")))
                self.respond_json(docs)
            elif path == "/api/work-items":
                docs = firestore_list_documents("work_items")
                docs.sort(key=lambda x: str(x.get("work_item_id", "")))
                self.respond_json(docs)
            elif path == "/api/bank-rec":
                docs = firestore_list_documents("bank_rec")
                docs.sort(key=lambda x: str(x.get("trade_ref", "")))
                self.respond_json(docs)
            elif path == "/api/stats":
                accs = firestore_list_documents("accounts")
                trades = firestore_list_documents("trades")
                wis = firestore_list_documents("work_items")
                brec = firestore_list_documents("bank_rec")
                self.respond_json({
                    "database": DATABASE_ID,
                    "project": PROJECT_ID,
                    "accounts_count": len(accs),
                    "trades_count": len(trades),
                    "work_items_count": len(wis),
                    "bank_rec_count": len(brec)
                })
            else:
                self.send_error(404, "API route not found")
        except Exception as e:
            self.respond_json({"error": str(e)}, status=500)

    def handle_api_post(self, path):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            data = json.loads(body)

            if path == "/api/reset":
                # Re-run seeder
                from seed_firestore import seed_all
                seed_all()
                self.respond_json({"status": "success", "message": "Baseline data restored successfully."})
            elif path == "/api/accounts":
                acct = str(data.get("account_no", "")).strip().upper()
                if not acct:
                    return self.respond_json({"error": "account_no required"}, status=400)
                firestore_upsert_document("accounts", acct, data)
                self.respond_json({"status": "created", "account_no": acct})
            elif path == "/api/trades":
                ref = str(data.get("trade_ref", "")).strip().upper()
                if not ref:
                    return self.respond_json({"error": "trade_ref required"}, status=400)
                firestore_upsert_document("trades", ref, data)
                self.respond_json({"status": "created", "trade_ref": ref})
            elif path == "/api/work-items":
                wid = str(data.get("work_item_id", "")).strip().upper()
                if not wid:
                    return self.respond_json({"error": "work_item_id required"}, status=400)
                firestore_upsert_document("work_items", wid, data)
                self.respond_json({"status": "created", "work_item_id": wid})
            elif path == "/api/bank-rec":
                ref = str(data.get("trade_ref", "")).strip().upper()
                if not ref:
                    return self.respond_json({"error": "trade_ref required"}, status=400)
                firestore_upsert_document("bank_rec", ref, data)
                self.respond_json({"status": "created", "trade_ref": ref})
            elif path == "/api/chat":
                session_id = str(data.get("session_id", "")).strip()
                message = str(data.get("message", "")).strip()
                if not message:
                    return self.respond_json({"error": "message required"}, status=400)
                result = call_ces_chat(session_id, message)
                self.respond_json(result)
            elif path == "/api/upload":
                filename = os.path.basename(data.get("filename", "upload.bin"))
                content_type = data.get("content_type", "application/octet-stream")
                b64_data = data.get("file_data", "")
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                file_bytes = base64.b64decode(b64_data)
                safe_name = f"{int(time.time())}_{filename}"
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                dest = UPLOAD_DIR / safe_name
                dest.write_bytes(file_bytes)
                self.respond_json({
                    "status": "success",
                    "filename": filename,
                    "saved_as": safe_name,
                    "size": len(file_bytes),
                    "content_type": content_type,
                    "url": f"/uploads/{safe_name}"
                })
            else:
                self.send_error(404)
        except Exception as e:
            self.respond_json({"error": str(e)}, status=500)

    def handle_api_put(self, path):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            data = json.loads(body)

            parts = path.strip("/").split("/")
            # e.g. ["api", "accounts", "ACC-1001"]
            if len(parts) >= 3:
                resource = parts[1]
                doc_id = urllib.parse.unquote(parts[2]).strip().upper()

                coll_map = {
                    "accounts": "accounts",
                    "trades": "trades",
                    "work-items": "work_items",
                    "bank-rec": "bank_rec"
                }
                coll = coll_map.get(resource)
                if coll:
                    firestore_upsert_document(coll, doc_id, data)
                    return self.respond_json({"status": "updated", "id": doc_id})

            self.send_error(404)
        except Exception as e:
            self.respond_json({"error": str(e)}, status=500)

    def respond_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

def run():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    server_address = ("0.0.0.0", PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, PortalHandler)
    print(f"State Street Mock Data Portal running at http://0.0.0.0:{PORT}")
    print(f"Connected to Firestore database '{DATABASE_ID}' in project '{PROJECT_ID}'")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
