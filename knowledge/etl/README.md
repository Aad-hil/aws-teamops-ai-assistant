# TeamOps AI — enterprise ETL incident KB

This collection adds **40 reconstructed incident scenarios** and **20 service-specific operational SOPs** for AWS Glue, Amazon Redshift, AWS Lambda, and S3/Step Functions orchestration.

**Important provenance rule:** No public incident log data or real customer production logs have been imported. Each `[SIMULATED]` log is invented to resemble a documented error class. The linked AWS references substantiate troubleshooting concepts, not the existence of any sample incident.

## Coverage
| Service | Incidents | SOPs |
| --- | ---: | ---: |
| AWS Glue | 12 | 5 |
| Amazon Redshift | 12 | 5 |
| AWS Lambda | 8 | 5 |
| ETL orchestration (Step Functions / S3) | 8 | 5 |
| **Total** | **40** | **20** |

## RAG usage policy
- For conceptual or troubleshooting queries, retrieve matching SOPs and incident examples.
- For live status or investigation, use an **authorized live diagnostics integration** first; the current customer-ingestion diagnostics does NOT query Glue or Redshift. Do not imply otherwise.
- Clearly label similarities to synthetic examples, request specific real logs before claiming a verified RCA, and separate hypothesis / observed evidence / remediation.
- Never propose an invented executable tool such as `read(path=...)` or `teamops-diagnostics ---get-recent-executions`. All command snippets have placeholders and must be adapted before use.
- Redshift `SYS_LOAD_ERROR_DETAIL` is a system view available to suitably authorized users; investigate actual permissions before running queries.
- Use only authorized resources. Avoid production reruns, table mutations, IAM changes or data deletion without explicit approval.

## Key references
- glue: https://docs.aws.amazon.com/glue/latest/dg/glue-troubleshooting-errors.html
- glueMemory: https://docs.aws.amazon.com/glue/latest/dg/monitor-profile-debug-oom-abnormalities.html
- glueBookmarks: https://docs.aws.amazon.com/glue/latest/dg/monitor-continuations.html
- redshift: https://docs.aws.amazon.com/redshift/latest/dg/t_Troubleshooting_load_errors.html
- redshiftErrors: https://docs.aws.amazon.com/redshift/latest/dg/r_Load_Error_Reference.html
- redshiftSys: https://docs.aws.amazon.com/redshift/latest/dg/SYS_LOAD_ERROR_DETAIL.html
- redshiftWlm: https://docs.aws.amazon.com/redshift/latest/dg/cm-c-wlm-dynamic-properties.html
- lambda: https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-invocation.html
- lambdaTimeout: https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html
- lambdaRetry: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html
- s3: https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
- step: https://docs.aws.amazon.com/step-functions/latest/dg/troubleshooting.html
- s3Events: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html

## Loading into the existing Knowledge Base
1. Ensure the S3 data source for Bedrock KB `9J62RRP7V6` uses prefix `knowledge-base/` and points to the intended bucket.
2. Sync **only** `knowledge/etl/` into `s3://teamops-ai-demo-databucket-ndrxe4zyoxfk/knowledge-base/etl/`; do not run a destructive `--delete` sync.
3. Start an ingestion job for data source `CK3FN9PTFQ` in `ap-southeast-2`; monitor to completion.
4. Evaluate retrieval using Glue OOM, Redshift COPY load error, Lambda throttle, and Step Functions integration queries.
5. Update the agent system prompt to accurately describe that these scenarios are synthetic, not historical facts.

## One-line CloudShell commands
```bash
aws s3 sync knowledge/etl/ s3://teamops-ai-demo-databucket-ndrxe4zyoxfk/knowledge-base/etl/ --region ap-southeast-2 --exclude "*" --include "*.md" --dryrun
aws s3 sync knowledge/etl/ s3://teamops-ai-demo-databucket-ndrxe4zyoxfk/knowledge-base/etl/ --region ap-southeast-2 --exclude "*" --include "*.md"
aws bedrock-agent start-ingestion-job --knowledge-base-id 9J62RRP7V6 --data-source-id CK3FN9PTFQ --region ap-southeast-2 --no-cli-pager
aws bedrock-agent list-ingestion-jobs --knowledge-base-id 9J62RRP7V6 --data-source-id CK3FN9PTFQ --region ap-southeast-2 --max-results 5 --query 'ingestionJobSummaries[].{Id:ingestionJobId,Status:status,Started:startedAt}' --output table --no-cli-pager
```
