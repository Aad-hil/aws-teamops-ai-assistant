"""Authenticated TeamOps AI Harness chat with user-owned conversation history."""
import base64
import json
import logging
import os
import time
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
HARNESS_ARN = os.environ["HARNESS_ARN"]
SESSIONS_TABLE = boto3.resource("dynamodb", region_name=REGION).Table(os.environ["CHAT_SESSIONS_TABLE"])
RUNTIME = boto3.client("bedrock-agentcore", region_name=REGION)
MAX_SAVED_MESSAGES = 60
MAX_SAVED_ANSWER_LENGTH = 6000


def _response(status, payload):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(payload),
    }


def _valid_session_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError):
        return None


def _owned_session(session_id, user_id):
    item = SESSIONS_TABLE.get_item(
        Key={"sessionId": session_id}, ConsistentRead=True
    ).get("Item")
    return item if item and item.get("userId") == user_id else None


def _read_body(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw) if isinstance(raw, str) else raw


def _get_history(user_id):
    items = []
    args = {
        "IndexName": "UserHistoryIndex",
        "KeyConditionExpression": Key("userId").eq(user_id),
        "ScanIndexForward": False,
        "ProjectionExpression": "sessionId, title, createdAt, updatedAt",
        "Limit": 50,
    }
    result = SESSIONS_TABLE.query(**args)
    for item in result.get("Items", []):
        items.append({
            "sessionId": item["sessionId"],
            "title": item.get("title") or "New conversation",
            "createdAt": int(item.get("createdAt", 0)),
            "updatedAt": int(item.get("updatedAt", 0)),
        })
    return _response(200, {"conversations": items})


def _get_conversation(session_id, user_id):
    item = _owned_session(session_id, user_id)
    if not item:
        return _response(404, {"error": "Conversation not found"})
    return _response(200, {
        "sessionId": session_id,
        "title": item.get("title") or "New conversation",
        "messages": item.get("messages") or [],
        "createdAt": int(item.get("createdAt", 0)),
        "updatedAt": int(item.get("updatedAt", 0)),
    })


def _delete_conversation(session_id, user_id):
    try:
        SESSIONS_TABLE.delete_item(
            Key={"sessionId": session_id},
            ConditionExpression="userId = :owner",
            ExpressionAttributeValues={":owner": user_id},
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return _response(404, {"error": "Conversation not found"})
        raise
    # Note: AgentCore runtime memory may have a separate retention lifecycle.
    return _response(200, {"deleted": True, "sessionId": session_id})


def _chat(body, user_id):
    if not isinstance(body, dict):
        return _response(400, {"error": "Expected a JSON object"})
    message = body.get("message")
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
        return _response(400, {"error": "Message must be 1-2000 characters"})
    message = message.strip()
    now = int(time.time())

    provided_id = body.get("sessionId")
    if provided_id is not None:
        session_id = _valid_session_id(provided_id)
        if not session_id:
            return _response(400, {"error": "Invalid session ID"})
        if not _owned_session(session_id, user_id):
            return _response(403, {"error": "Session access denied"})
    else:
        session_id = str(uuid.uuid4())
        SESSIONS_TABLE.put_item(
            Item={
                "sessionId": session_id,
                "userId": user_id,
                "title": message[:70],
                "createdAt": now,
                "updatedAt": now,
                "messages": [],
            },
            ConditionExpression="attribute_not_exists(sessionId)",
        )

    result = RUNTIME.invoke_harness(
        harnessArn=HARNESS_ARN,
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": message}]}],
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

    # Save displayed conversation text only after a successful agent response.
    # Bound history growth to stay comfortably under DynamoDB's 400-KB item limit.
    saved = SESSIONS_TABLE.update_item(
        Key={"sessionId": session_id},
        UpdateExpression=(
            "SET #messages = list_append(if_not_exists(#messages, :empty), :added), "
            "#updatedAt = :now, #title = if_not_exists(#title, :title) REMOVE expiresAt"
        ),
        ConditionExpression="userId = :owner AND attribute_exists(sessionId)",
        ExpressionAttributeNames={
            "#messages": "messages",
            "#updatedAt": "updatedAt",
            "#title": "title",
        },
        ExpressionAttributeValues={
            ":empty": [],
            ":added": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": answer[:MAX_SAVED_ANSWER_LENGTH]},
            ],
            ":now": now,
            ":title": message[:70],
            ":owner": user_id,
        },
        ReturnValues="ALL_NEW",
    ).get("Attributes", {})

    history = saved.get("messages", [])
    if len(history) > MAX_SAVED_MESSAGES:
        SESSIONS_TABLE.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #messages = :recent",
            ConditionExpression="userId = :owner",
            ExpressionAttributeNames={"#messages": "messages"},
            ExpressionAttributeValues={
                ":recent": history[-MAX_SAVED_MESSAGES:],
                ":owner": user_id,
            },
        )
    return _response(200, {"answer": answer, "sessionId": session_id})


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

        # Self-registered users must be approved into the operations group.
        groups = claims.get("cognito:groups", [])
        if isinstance(groups, str):
            raw_groups = groups.strip().strip("[]")
            groups = [part.strip().strip("\\\"'") for part in raw_groups.split(",") if part.strip()]
        if not isinstance(groups, list) or "teamops-users" not in groups:
            return _response(403, {"error": "Account awaiting administrator approval"})

        route = event.get("routeKey", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if route == "GET /conversations":
            return _get_history(user_id)

        if route in ("GET /conversations/{sessionId}", "DELETE /conversations/{sessionId}"):
            session_id = _valid_session_id((event.get("pathParameters") or {}).get("sessionId"))
            if not session_id:
                return _response(400, {"error": "Invalid session ID"})
            return (_get_conversation(session_id, user_id) if method == "GET"
                    else _delete_conversation(session_id, user_id))

        if route == "POST /chat":
            try:
                body = _read_body(event)
            except (ValueError, TypeError, UnicodeDecodeError):
                return _response(400, {"error": "Invalid JSON request"})
            return _chat(body, user_id)

        return _response(404, {"error": "Route not found"})
    except ClientError:
        LOG.exception("AWS service error")
        return _response(502, {"error": "Chat service unavailable"})
    except Exception:
        LOG.exception("TeamOps chat invocation failed")
        return _response(502, {"error": "Chat service unavailable"})
