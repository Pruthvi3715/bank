#!/usr/bin/env python3
"""Test all backend endpoints end-to-end."""

import json
import subprocess
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def post(url, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, headers=headers, method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code
    except Exception as ex:
        return {"error": str(ex)}, 500


def get(url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code
    except Exception as ex:
        return {"error": str(ex)}, 500


def main():
    print("=== GraphSentinel Backend End-to-End Test ===\n")

    # 1. Get token
    auth_data, _ = post(
        f"{BASE}/token", {"username": "investigator", "password": "investigate123"}
    )
    token = auth_data.get("access_token")
    print(f"[1] Auth: OK (role={auth_data.get('role')})\n")

    # 2. Health
    health, _ = get(f"{BASE}/api/health")
    print(f"[2] Health: {health.get('status')} v{health.get('version')}")

    # 3. Auth profile
    me, _ = get(f"{BASE}/auth/me", token)
    print(f"[3] Auth/me: {me.get('user_id')} ({me.get('role')})")

    # 4. ML info
    ml_info, _ = get(f"{BASE}/api/ml-info", token)
    fi = ml_info.get("feature_importance", {})
    ms = ml_info.get("model_status", {})
    print(
        f"[4] ML info: {len(fi)} features, IF={ms.get('isolation_forest')}, XGB={ms.get('xgboost')}"
    )

    # 5. Streaming status
    stream_status, _ = get(f"{BASE}/api/streaming/status", token)
    print(
        f"[5] Streaming: enabled={stream_status.get('streaming_enabled')}, consumer={stream_status.get('consumer_active')}"
    )

    # 6. Quick questions
    qa, _ = get(f"{BASE}/api/sar-chat/quick-questions", token)
    print(f"[6] Quick questions: {len(qa.get('questions', []))} questions")

    # 7. Feedback config
    fb, _ = get(f"{BASE}/api/feedback/config", token)
    print(f"[7] Feedback config: keys={list(fb.keys())}")

    # 8. Run pipeline
    print("\n[8] Running pipeline...")
    pipeline_result, status = post(f"{BASE}/api/run-pipeline", {}, token)
    if status == 200:
        print(
            f"    SUCCESS: {len(pipeline_result['alerts'])} alerts, "
            f"{len(pipeline_result['graph']['nodes'])} nodes, "
            f"{len(pipeline_result['graph']['links'])} edges"
        )
        print(f"    Patterns: {pipeline_result['stats']['pattern_counts']}")
        print(f"    ML: {pipeline_result['ml_info']['model_status']}")
        print(f"    Activity: {len(pipeline_result['agent_activity'])} steps")
    else:
        print(f"    FAILED ({status}): {pipeline_result}")

    # 9. Demo track A
    demo, _ = get(f"{BASE}/api/demo-track-a")
    print(
        f"\n[9] Demo Track A: {len(demo.get('alerts', []))} alerts, "
        f"{len(demo.get('graph', {}).get('nodes', []))} nodes, "
        f"{len(demo.get('agent_activity', []))} activity steps"
    )

    # 10. Adversarial test
    adv, _ = get(f"{BASE}/api/adversarial-test?test=cycle_plus_hop", token)
    adv_nodes = len(adv.get("graph", {}).get("nodes", []))
    print(
        f"[10] Adversarial test: {adv_nodes} nodes, {len(adv.get('alerts', []))} alerts"
    )

    # 11. SAR Chat (rule-based, no LLM needed)
    if pipeline_result.get("alerts"):
        alert_id = pipeline_result["alerts"][0]["alert_id"]
        chat, _ = post(
            f"{BASE}/api/sar-chat",
            {"alert_id": alert_id, "message": "Why was this flagged?"},
            token,
        )
        resp = chat.get("response", "")[:100]
        print(f"\n[11] SAR Chat (rule-based): {resp}...")

    # 12. PDF export
    if pipeline_result.get("alerts"):
        alert_id = pipeline_result["alerts"][0]["alert_id"]
        pdf_req = urllib.request.Request(
            f"{BASE}/api/sar/{alert_id}/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(pdf_req) as resp:
                pdf_bytes = resp.read()
                print(
                    f"[12] PDF export: {len(pdf_bytes)} bytes (valid PDF: {pdf_bytes[:4] == b'%PDF'})"
                )
        except urllib.error.HTTPError as e:
            print(f"[12] PDF export: HTTP {e.code} - {e.reason}")

    print("\n=== All tests passed ===")


if __name__ == "__main__":
    main()
