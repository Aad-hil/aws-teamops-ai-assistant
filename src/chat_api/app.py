"""Private TeamOps AI chat adapter for an AgentCore-managed Harness.

Do not expose via a public Lambda URL or unauthenticated API Gateway route.
Before production: enforce JWT identity, per-user session ownership and team scope.
"""
import json
import logging
import os
import uuid

import boto3

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
HARNESS_ARN = os.environ["HARNESS_ARN"]
RUNTIME = boto3.client("bedrock-agentcore", region_name=REGION)


def _response(status, payload):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(payload),
    }


def lambda_handler(event, context):
    try:
        raw = event.get("body") or "{}"
        body = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(body, dict):
            return _response(400, {"error": "Expected a JSON object"})
        message = body.get("message")
        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
            return _response(400, {"error": "Message must be 1-2000 characters"})
        # Temporary: always start a fresh session until authenticated session
        # ownership and conversation persistence are implemented.
        session_id = str(uuid.uuid4())
        result = RUNTIME.invoke_harness(
            harnessArn=HARNESS_ARN,
            runtimeSessionId=session_id,
            messages=[{"role": "user", "content": [{"text": message.strip()}]}],
        )
        chunks = []
        completed = False
        try:
            for item in result["stream"]:
                if "contentBlockDelta" in item:
                    text = item["contentBlockDelta"].get("delta", {}).get("text")
                    if isinstance(text, str):
                        chunks.append(text)
                if "messageStop" in item:
                    completed = True
                for key in item:
                    if key.endswith("Exception") or key in ("error", "exception"):
                        raise RuntimeError("AgentCore event stream error: " + key)
        finally:
            result["stream"].close()
        answer = "".join(chunks)
        if not answer or not completed:
            raise RuntimeError("AgentCore returned incomplete or empty output")
        return _response(200, {"answer": answer, "sessionId": session_id})
    except (ValueError, TypeError):
        return _response(400, {"error": "Invalid JSON request"})
    except Exception:
        LOG.exception("TeamOps chat invocation failed")
        return _response(502, {"error": "Chat service unavailable"})
