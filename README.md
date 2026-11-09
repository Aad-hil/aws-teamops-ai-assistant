# TeamOps AI — AWS Agentic Operations Assistant

A synthetic-data operations assistant built with Amazon Bedrock AgentCore, Amazon Bedrock Knowledge Bases, AWS Lambda, API Gateway, Cognito, DynamoDB, S3, and a React/Vite interface hosted on CloudFront.

**Demo environment:** AWS region `ap-southeast-2` (Sydney). This repository is a demo, not a production-ready multi-tenant service.

## Features

- **AI Assistant:** Ask questions about ingestion executions, failures and runbooks via AgentCore Harness.
- **Persistent conversations:** User-owned sessions, previous-chat sidebar, reopen and delete history records.
- **Rich responses:** Markdown, GitHub-flavored tables, code blocks with copy, and safe HTTP(S) links.
- **Diagnostics:** Read-only execution summaries from the synthetic customer-ingestion workflow.
- **Knowledge Base:** Search synthetic SOPs and troubleshooting documents using Bedrock retrieval.
- **Authentication:** Amazon Cognito sign-in, first-time password change, JWT-protected API routes, and group-gated Dashboard API.

## Architecture

```text
Browser
  |
  +-- CloudFront -> S3-hosted React/Vite
  |
  +-- API Gateway HTTP API (Cognito JWT authorizer)
       |
       +-- POST /chat ----------------------------> Chat Lambda -> AgentCore Harness
       |                                              |
       |                                              +-> DynamoDB ChatSessionsTable
       |
       +-- GET /conversations --------------------> Chat Lambda -> DynamoDB
       +-- GET /conversations/{sessionId} --------> Chat Lambda -> DynamoDB
       +-- DELETE /conversations/{sessionId} -----> Chat Lambda -> DynamoDB
       |
       +-- GET /diagnostics ----------------------> Dashboard Lambda -> Diagnostics Lambda -> DynamoDB ExecutionsTable
       +-- POST /knowledge -----------------------> Dashboard Lambda -> KB Retrieval Lambda -> Bedrock Knowledge Base

Synthetic ingestion: S3 input/ -> Processor Lambda -> DynamoDB ExecutionsTable + S3 processed/
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `template.yaml` | SAM-defined Lambda functions, DynamoDB tables and IAM policies |
| `src/chat_api/` | Authenticated AgentCore Harness chat and conversation history |
| `src/dashboard_api/` | Group-authorized diagnostics and knowledge API adapter |
| `src/diagnostics/` | Internal read-only execution summaries |
| `src/kb_retrieval/` | Internal Bedrock Knowledge Base retrieval |
| `src/processor/` | Synthetic S3 ingestion processor |
| `web/` | React/Vite single-page application |
| `samples/` | Synthetic CSV samples |
| `docs/` | Additional implementation guides |

## Prerequisites

- AWS credentials authorized to deploy CloudFormation/SAM, IAM, Lambda, DynamoDB, S3, and supporting resources.
- An existing Bedrock Knowledge Base ID and AgentCore Harness ARN.
- A configured Cognito User Pool and HTTP API Gateway JWT authorizer.
- Node.js 20+ and npm for the frontend; Python 3.13 and AWS SAM CLI for backend deployment.

**Note:** The deployed API Gateway, Cognito pool, CloudFront distribution, and frontend bucket were provisioned/configured separately from this SAM template. They are **not fully reproducible by running `sam deploy` alone**. Replace environment-specific IDs in `web/src/main.tsx` and `web/src/DashboardPanel.tsx` before using another account.

## Backend deployment

```bash
sam validate --lint
sam build
sam deploy \
  --stack-name teamops-ai-demo \
  --region ap-southeast-2 \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides HarnessArn=<EXISTING_HARNESS_ARN> KnowledgeBaseId=<EXISTING_KB_ID>
```

Verify the ChatSessionsTable and its UserHistoryIndex are ACTIVE before loading history. Configure the existing API Gateway integrations and JWT-protected routes to target ChatApiFunction and DashboardApiFunction; restrict CORS to your CloudFront origin. Do not publicly expose internal Diagnostics or KnowledgeRetrieval functions.

## Frontend build and hosting

```bash
cd web
npm install
npm run build
```

For the existing demo deployment, upload `web/dist/` to the dedicated frontend S3 bucket and invalidate CloudFront. Configure the bucket and distribution IDs for your account. Generated assets and `node_modules/` are ignored by Git.

## Security and limits

- The HTTP API JWT authorizer authenticates callers; the Chat Lambda binds conversations to the Cognito `sub`. The Dashboard Lambda additionally checks the `teamops-users` group claim.
- **Production hardening required:** enforce team/project authorization in chat and every downstream agent tool; an authenticated JWT alone does not guarantee tenant isolation.
- The diagnostics tool currently filters to demo `data-engineering/customer-ingestion` data. It is not a general-purpose tenant-aware query service.
- Deleting a chat removes its DynamoDB record but does **not** guarantee deletion of any independently retained AgentCore memory, traces, or logs.
- History is limited to 50 recent conversations per listing and 60 displayed messages per conversation. Old conversations without saved transcript records cannot be reconstructed automatically.
- Passwords, JWTs, and AWS credentials must not be committed. Use dedicated roles and review IAM/CORS before enabling public access.
- Synthetic examples and retrieved SOPs are not production remediation instructions. Require human approval for potentially destructive operational changes.

## Functional acceptance checks

1. Sign in as a Cognito user, including a first-time password-change challenge if applicable.
2. Open a new chat, send a prompt, then ask a follow-up in the same session.
3. Reload; reopen the saved chat from the sidebar.
4. Delete a chat; verify it disappears and is no longer retrievable.
5. Open Diagnostics and verify sample execution records.
6. Search Knowledge Base for `SCHEMA_MISMATCH` and verify the retrieved SOP.
7. Request a Markdown table/code block and verify safe rendering.

## Cleanup

Review stack resources and costs before removing the sandbox. CloudFormation teardown may not remove separately configured API Gateway, Cognito, CloudFront, KB, or AgentCore resources.
