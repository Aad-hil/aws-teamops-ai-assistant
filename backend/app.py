"""TeamOps web API. Development-only: add Cognito authentication before exposing publicly."""
import json
import os
import uuid
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="TeamOps AI API")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str

@app.get("/api/health")
def health():
    return {"status": "ok", "agent_configured": bool(os.getenv("AGENT_RUNTIME_ARN"))}

@app.post("/api/chat")
def chat(request: ChatRequest):
    arn = os.getenv("AGENT_RUNTIME_ARN")
    if not arn:
        raise HTTPException(503, "AGENT_RUNTIME_ARN is not configured")
    try:
        session_id = str(uuid.UUID(request.session_id))
    except ValueError:
        raise HTTPException(422, "session_id must be a UUID")
    try:
        client = boto3.client("bedrock-agentcore", region_name=os.getenv("AWS_REGION", "ap-southeast-2"))
        response = client.invoke_agent_runtime(
            agentRuntimeArn=arn,
            runtimeSessionId=session_id,
            payload=json.dumps({"prompt": request.message}).encode(),
            contentType="application/json",
            accept="application/json",
        )
        stream = response["response"]
        raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
        body = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        try:
            parsed = json.loads(body)
            reply = parsed.get("response") or parsed.get("output") or parsed.get("answer") or body if isinstance(parsed, dict) else body
        except json.JSONDecodeError:
            reply = body
        return {"reply": str(reply), "session_id": session_id}
    except Exception:
        # Do not expose IAM errors, ARNs, or other internal exception details to browsers.
        import logging
        logging.exception("AgentCore invocation failed")
        raise HTTPException(502, "Agent invocation failed; inspect backend logs")
