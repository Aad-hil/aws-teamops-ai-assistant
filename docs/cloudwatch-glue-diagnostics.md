# CloudWatch log correlation for the TeamOps Glue demo

This extension is for the existing **Python shell** job `teamops-glue-demo-etl`, not all CloudWatch or Glue jobs.

AWS Glue Python shell logs default to **/aws-glue/python-jobs/error** and **/aws-glue/python-jobs/output**. See https://docs.aws.amazon.com/glue/latest/dg/add-job-python.html.

## Threat model and limitations
- Lambda can only resolve a run ID against `GLUE_JOB_NAME` configured at deployment, using Glue GetJobRun.
- Tool input accepts only `{"action":"get_run_logs","run_id":"jr_..."}`.
- FilterLogEvents searches only run-ID-prefixed streams under the two fixed groups, within the actual run's time window (plus two minutes, maximum 24h).
- This Lambda reads existing logs only. No log delivery, retention settings, new log streams, metric filters, or AWS write permissions.
- CloudWatch logs are untrusted content. Output is truncated and common credential-shaped fragments are masked, but it is **not a comprehensive sensitive-data sanitizer**. The log groups are shared by many Python shell jobs: IAM grants group-level access, while run scoping is enforced in Lambda. Do not deploy in a multi-tenant production account without stronger authorization and isolation.
- `FilterLogEvents` is paginated. The function caps its results and sets `truncated=true` when there is a next page. Absence of events is not proof of absence of an error.
- Check that the run-ID stream naming convention matches actual CloudWatch log streams in your account. If run IDs are not stream prefixes, the function will show zero events rather than widen scope.
- The function should only be attached as a private AgentCore Gateway Lambda tool with the existing auth and a tightly scoped Gateway IAM role.

## Before deployment — CloudShell single-line commands
```bash
aws logs describe-log-groups --log-group-name-prefix /aws-glue/python-jobs/ --region ap-southeast-2 --query 'logGroups[].logGroupName' --output table --no-cli-pager
aws logs describe-log-streams --log-group-name /aws-glue/python-jobs/error --order-by LastEventTime --descending --limit 5 --region ap-southeast-2 --query 'logStreams[].logStreamName' --output table --no-cli-pager
```
This inspection is important: some Glue configurations use custom log groups, which are intentionally unsupported in this first stage.

## Deployment approach
This branch is stacked onto `feature/glue-readonly-diagnostics` (PR #10) and includes its Glue diagnostics Lambda and SAM changes. Use an approved CloudFormation changeset and preserve the existing stack parameters. The CloudWatch resource is enabled only if GlueDiagnosticJobName is configured.

One-line deployment preview after tests and SAM validation:
```bash
sam deploy --stack-name teamops-ai-demo --region ap-southeast-2 --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides KnowledgeBaseId=9J62RRP7V6 HarnessArn=arn:aws:bedrock-agentcore:ap-southeast-2:241227970144:harness/Teamops_ai_agent-dYfltEVgwy GlueDiagnosticJobName=teamops-glue-demo-etl --no-execute-changeset --no-confirm-changeset --no-fail-on-empty-changeset
```
Do not deploy until the log-group/stream names and IAM scope are reviewed.

## Gateway tool contract
```json
[{"name":"get_glue_run_logs","description":"Read bounded CloudWatch error and output logs for a verified TeamOps demo Glue Python shell job run. Requires run_id from Glue diagnostics; no other jobs or log groups.","inputSchema":{"type":"object","properties":{"action":{"type":"string","enum":["get_run_logs"]},"run_id":{"type":"string","description":"Exact Glue job run ID returned by live Glue diagnostics"}},"required":["action","run_id"]}}]
```

Expected workflow: the agent first calls Glue run diagnostics to obtain a real `run_id`, then calls this logs tool, then retrieves an appropriate KB SOP. Label each evidence source separately.

## Acceptance tests
1. Query the latest known FAILED Glue run ID; correlate its log evidence with `DEMO_ETL_VALIDATION_FAILURE`.
2. Query the successful Glue run; ensure no fabricated error.
3. Supply an unknown run ID; the Glue API must reject it and no logs should be returned.
4. Supply arbitrary group name or job name; tool must reject parameters.
5. Request Redshift logs; tool must not respond with Python-shell Glue logs.
6. Validate Gateway execution role can invoke only the authorized Lambda, and verify CloudWatch searches have no write permissions.
