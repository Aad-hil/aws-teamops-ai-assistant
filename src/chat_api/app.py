"""Authenticated TeamOps AI chat adapter for AgentCore Harness."""
import json
import logging
import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
HARNESS_ARN = os.environ["HARNESS_ARN"]
SESSIONS_TABLE = boto3.resource("dynamodb", region_name=REGION).Table(os.environ["CHAT_SESSIONS_TABLE"])
RUNTIME = boto3.client("bedrock-agentcore", region_name=REGION)
SESSION_TTL_SECONDS = 86400


def _response(status, payload):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(payload),
    }


def lambda_handler(event, context):
    try:
        event = event if isinstance(event, dict) else {}
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
        )
        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id:
            return _response(401, {"error": "Unauthorized"})

        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64
            raw = base64.b64decode(raw).decode("utf-8")
        body = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(body, dict):
            return _response(400, {"error": "Expected a JSON object"})
        message = body.get("message")
        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
            return _response(400, {"error": "Message must be 1-2000 characters"})

        session_id = body.get("sessionId")
        now = int(time.time())
        if session_id is not None:
            if not isinstance(session_id, str):
                return _response(400, {"error": "Invalid session ID"})
            try:
                session_id = str(uuid.UUID(session_id))
            except (ValueError, AttributeError):
                return _response(400, {"error": "Invalid session ID"})
            item = SESSIONS_TABLE.get_item(
                Key={"sessionId": session_id}, ConsistentRead=True
            ).get("Item")
            if (
                not item
                or item.get("userId") != user_id
                or int(item.get("expiresAt", 0)) <= now
            ):
                return _response(403, {"error": "Session access denied"})
        else:
            session_id = str(uuid.uuid4())
            SESSIONS_TABLE.put_item(
                Item={
                    "sessionId": session_id,
                    "userId": user_id,
                    "expiresAt": now + SESSION_TTL_SECONDS,
                },
                ConditionExpression="attribute_not_exists(sessionId)",
            )

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
                    delta = item["contentBlockDelta"].get("delta", {}).get("text")
                    if isinstance(delta, str):
                        chunks.append(delta)
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
    except ClientError:
        LOG.exception("AWS service error")
        return _response(502, {"error": "Chat service unavailable"})
    except Exception:
        LOG.exception("TeamOps chat invocation failed")
        return _response(502, {"error": "Chat service unavailable"})
