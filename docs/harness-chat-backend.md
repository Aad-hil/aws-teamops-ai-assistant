# TeamOps AI — Harness chat backend (work in progress)

This branch contains a private Python Lambda adapter for the existing AgentCore Harness `Teamops_ai_agent` in `ap-southeast-2`.

## Fetch in AWS CloudShell (no office laptop installation)

```bash
git clone --branch feature/harness-chat-backend https://github.com/Aad-hil/aws-teamops-ai-assistant.git
cd aws-teamops-ai-assistant
```

If the repository is already cloned:

```bash
git fetch origin
git switch feature/harness-chat-backend || git switch -c feature/harness-chat-backend --track origin/feature/harness-chat-backend
git pull --ff-only
```

## Current implementation

- `src/chat_api/app.py`: Lambda handler using `boto3.client("bedrock-agentcore").invoke_harness`, consumes `contentBlockDelta` event-stream chunks.
- `src/chat_api/requirements.txt`: boto3 version supporting `InvokeHarness`.
- Environment variable `HARNESS_ARN` must be configured when deploying.
- Each invocation currently uses a fresh session; multi-turn chat is **not yet implemented**.

## Before connecting CloudFront

1. Add a SAM Lambda resource with least-privilege `bedrock-agentcore:InvokeHarness` scoped to the exact Harness ARN, and package dependencies.
2. Configure Cognito JWT authorization at API Gateway. Do not expose a public unauthenticated Lambda URL or route.
3. Derive the user's identity from verified JWT claims, bind sessions to that identity, and enforce team-level data access. Do not trust a browser-provided team ID or session ID.
4. Add a CloudFront `/api/*` behavior to the authenticated API origin and update the frontend client.
5. Test end-to-end behavior, logging, limits, and costs.

**Not deployed yet.** The current files are version-controlled source only. Use synthetic data for the demo.
