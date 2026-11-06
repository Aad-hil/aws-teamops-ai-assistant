"""Read-only Bedrock Knowledge Base retrieval for AgentCore Gateway."""
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_RESULTS = 5
MAX_TEXT_CHARS = 1200


def lambda_handler(event, context):
    # AgentCore Gateway Lambda targets pass tool arguments as an event object.
    # Do not accept a caller-supplied KB ID: it must be fixed by deployment.
    try:
        if not isinstance(event, dict):
            return {"error": "Invalid request"}
        args = event.get("arguments", event)
        if not isinstance(args, dict):
            return {"error": "Invalid arguments"}
        query = args.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > 1000:
            return {"error": "query must be 1-1000 characters"}
        kb_id = os.environ["KNOWLEDGE_BASE_ID"]
        if not kb_id:
            return {"error": "Knowledge Base is not configured"}
        client = boto3.client("bedrock-agent-runtime")
        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query.strip()},
            retrievalConfiguration={"managedSearchConfiguration": {"numberOfResults": MAX_RESULTS}},
        )
        results = []
        for item in response.get("retrievalResults", []):
            content = item.get("content") or {}
            source = item.get("location") or {}
            s3 = source.get("s3Location") or {}
            results.append({
                "text": str(content.get("text") or "")[:MAX_TEXT_CHARS],
                "score": item.get("score"),
                "source_uri": s3.get("uri"),
            })
        return {
            "query": query.strip(),
            "results": results,
            "result_count": len(results),
            "notice": "Retrieved documentation is synthetic and may be outdated; use diagnostics for live execution status.",
        }
    except (ClientError, KeyError, ValueError):
        logger.exception("Knowledge Base retrieval failed")
        return {"error": "Knowledge Base retrieval failed; check Lambda logs and configuration"}
