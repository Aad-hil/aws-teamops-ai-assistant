# AWS Glue read-only diagnostics (Phase 1)

## Scope and safety
This feature adds an **internal** Lambda intended for a future AgentCore Gateway tool binding. It queries only a single deployment-configured AWS Glue job, not arbitrary user-provided names. The Lambda supports **recent_runs** (GetJobRuns) and **get_run** (GetJobRun), both read-only. The execution role is restricted to the configured Glue job ARN. It returns allowlisted fields only and excludes job arguments and sensitive configuration. No resource modification or IAM broadening is needed beyond the specified job read actions.

**Important:** This does not connect the Gateway or expose an HTTP endpoint. Do not expose the function publicly. Gateway users must be authorized for this job; the deployment-wide job allowlist is not per-user authorization. Configure Gateway auth, IAM resource policy and team/project access control before binding it.

## Before deployment
- Choose an **existing authorized Glue job** in ap-southeast-2, and use its exact job name in GlueDiagnosticJobName.
- Deploy the current SAM template while preserving all existing stack parameters (HarnessArn, KnowledgeBaseId).
- If there is no permitted Glue job, leave the parameter empty. The function will fail closed, and its IAM statement will match no actual Glue job.
- Review whether Glue error messages might contain sensitive upstream data. The handler truncates text but does not perform comprehensive PII redaction; use synthetic or approved demo jobs and traces only.

## Single-line CloudShell commands
```bash
cd ~/teamops-signup && git fetch origin feature/glue-readonly-diagnostics && git switch -C feature/glue-readonly-diagnostics FETCH_HEAD
python3 -m pytest -q tests/test_glue_diagnostics.py
sam validate --lint
sam build
sam deploy --stack-name teamops-ai-demo --region ap-southeast-2 --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides KnowledgeBaseId=9J62RRP7V6 HarnessArn=arn:aws:bedrock-agentcore:ap-southeast-2:241227970144:harness/Teamops_ai_agent-dYfltEVgwy GlueDiagnosticJobName=REPLACE_WITH_APPROVED_GLUE_JOB --no-confirm-changeset
aws cloudformation describe-stacks --stack-name teamops-ai-demo --region ap-southeast-2 --query 'Stacks[0].Outputs[?OutputKey==`GlueDiagnosticsFunctionArn`]' --output table
```
Do not execute the deployment command literally until the placeholder has been replaced by an authorized Glue job. SAM deployment may update existing resources; inspect the change set if you require stronger change control.

## Gateway target contract
Lambda accepts `{"action":"recent_runs","limit":5}` or `{"action":"get_run","run_id":"jr_..."}`. A user-supplied `job_name` is allowed **only** when exactly equal to the deployment configured Glue job.

Suggested Gateway input schema:
```json
{"type":"object","properties":{"action":{"type":"string","enum":["recent_runs","get_run"]},"limit":{"type":"integer","minimum":1,"maximum":10},"run_id":{"type":"string"}},"required":["action"]}
```

Bind via the existing AgentCore Gateway with its existing authorization and a scoped Lambda invocation permission. Actual Gateway target configuration depends on the current Gateway settings; inspect it before applying changes.

## Acceptance tests
1. Ask for latest executions for the allowlisted Glue job and compare run IDs/status to the Glue console.
2. Ask for a single approved run_id and compare result.
3. Ask for another job name; must be rejected without calling Glue.
4. Ask to start, retry, or delete a job; must be rejected.
5. Ask for Redshift or Step Functions live status; agent must state integrations aren't enabled yet.
6. Ask about an OOM incident; assistant should use KB SOP plus confirmed live Glue run facts, not claim actual CloudWatch logs were queried.
