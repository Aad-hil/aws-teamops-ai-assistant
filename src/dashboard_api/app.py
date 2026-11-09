import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lambda_client = boto3.client("lambda")
DIAGNOSTICS_FUNCTION = os.environ["DIAGNOSTICS_FUNCTION"]
KNOWLEDGE_FUNCTION = os.environ["KNOWLEDGE_FUNCTION"]
ALLOWED_GROUP = os.environ["ALLOWED_GROUP"]


def response(status, data):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(data),
    }


def invoke_internal(function_name, payload):
    result = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )
    if result.get("FunctionError"):
        raise RuntimeError("Internal Lambda failed")
    data = json.loads(result["Payload"].read())
    if not isinstance(data, dict) or "error" in data:
        raise RuntimeError("Internal service returned an error")
    return data


def lambda_handler(event, context):
    event = event if isinstance(event, dict) else {}
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    if not claims.get("sub"):
        return response(401, {"error": "Unauthorized"})

    groups = claims.get("cognito:groups", [])
    if isinstance(groups, str):
        value = groups.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        groups = [
            group.strip().strip("\\\"'")
            for group in value.split(",")
            if group.strip()
        ]
    if not isinstance(groups, list):
        groups = []
    if ALLOWED_GROUP not in groups:
        logger.warning("Dashboard access denied: missing required Cognito group")
        return response(403, {"error": "Access denied"})

    route = event.get("routeKey", "")
    try:
        if route == "GET /diagnostics":
            params = event.get("queryStringParameters") or {}
            try:
                limit = int(params.get("limit", "10"))
            except (TypeError, ValueError):
                return response(400, {"error": "Invalid limit"})
            if not 1 <= limit <= 25:
                return response(400, {"error": "Limit must be 1-25"})
            return response(200, invoke_internal(DIAGNOSTICS_FUNCTION, {"limit": limit}))

        if route == "POST /knowledge":
            body = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                import base64
                body = base64.b64decode(body).decode("utf-8")
            try:
                payload = json.loads(body) if isinstance(body, str) else body
            except (ValueError, TypeError):
                return response(400, {"error": "Invalid JSON"})
            if not isinstance(payload, dict):
                return response(400, {"error": "Expected JSON object"})
            query = payload.get("query")
            if not isinstance(query, str) or not 1 <= len(query.strip()) <= 1000:
                return response(400, {"error": "Query must be 1-1000 characters"})
            return response(200, invoke_internal(KNOWLEDGE_FUNCTION, {"query": query.strip()}))
        return response(404, {"error": "Route not found"})
    except (ClientError, RuntimeError):
        logger.exception("Dashboard service invocation failed")
        return response(502, {"error": "Dashboard service unavailable"})
