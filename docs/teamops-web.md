# TeamOps AI Web Chat (development MVP)

## Run locally
Requires Python 3.11+, Node.js 20+, AWS credentials with bedrock-agentcore:InvokeAgentRuntime.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export AWS_REGION=ap-southeast-2
export AGENT_RUNTIME_ARN='arn:aws:bedrock-agentcore:ap-southeast-2:ACCOUNT_ID:runtime/ACTUAL_RUNTIME_ID'
uvicorn backend.app:app --reload --port 8000
```
In another terminal:
```bash
cd web
npm install
npm run dev
```
Open http://localhost:5173.

**Important:** The API payload `{"prompt": "..."}` is an integration assumption. Check the deployed AgentCore harness request/response contract; adapt the backend adapter if your runtime expects another payload shape. The frontend's chat history is in browser memory only; AgentCore session ID is reused for follow-ups. Verify that the harness maps that ID to its AgentCore Memory.

## Security gate before production
This MVP intentionally has no public deployment. Add Cognito JWT verification on every backend request, derive team membership server-side, enforce team filtering in diagnostics and KB retrieval Lambdas, and bind sessions to authenticated user IDs. Never accept team IDs from the browser as authorization. Use TLS, restricted CORS, rate limiting and request logging without sensitive prompts. Do not expose AWS credentials or the agent runtime ARN in the frontend.

The diagnostics and knowledge tools remain invoked by the existing AgentCore Gateway; the browser only calls FastAPI.
