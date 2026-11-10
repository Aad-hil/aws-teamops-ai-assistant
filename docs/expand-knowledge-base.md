# Expanding the TeamOps AI Bedrock Knowledge Base

This repository maintains synthetic customer-ingestion runbooks under `knowledge/`. The initial docs are `project-overview.md` and `troubleshooting.md`; the expanded pack adds six targeted guides for ingestion errors, diagnostics, and safe operation.

## Before uploading

The existing Knowledge Base is `9J62RRP7V6` in `ap-southeast-2`. Its **S3 source bucket and prefix are NOT defined in this repository**, so discover them in AWS rather than guessing.

Read-only commands (each is one CloudShell line):

```bash
aws bedrock-agent list-data-sources --knowledge-base-id 9J62RRP7V6 --region ap-southeast-2 --query 'dataSourceSummaries[].{id:dataSourceId,name:name,status:status}' --output table
```

Select the S3 source from the result and inspect its bucket ARN and optional inclusion prefix:

```bash
aws bedrock-agent get-data-source --knowledge-base-id 9J62RRP7V6 --data-source-id REPLACE_WITH_DATA_SOURCE_ID --region ap-southeast-2 --query 'dataSource.dataSourceConfiguration' --output json
```

Check that source configuration is `S3`. `bucketArn` identifies the correct document bucket, and `inclusionPrefixes` determines where the KB looks for objects. Do **not** upload documents to the website hosting bucket or synthetic ingestion data bucket by assumption.

## Publish the new knowledge documents

Update local checkout to this feature branch and upload only the new six files to a path covered by the existing S3 data source:

```bash
cd ~/teamops-signup && git fetch origin feature/expanded-ingestion-knowledge && git switch -c feature/expanded-ingestion-knowledge FETCH_HEAD
```

Preview objects that would be uploaded (replace placeholders using the inspected S3 configuration):

```bash
aws s3 sync ~/teamops-signup/knowledge/ s3://REPLACE_KB_BUCKET/REPLACE_KB_PREFIX/ --exclude "*" --include "sop-*.md" --include "faq-*.md" --dryrun --region ap-southeast-2
```

Upload after confirming the target path and that no existing source documents will be overwritten:

```bash
aws s3 sync ~/teamops-signup/knowledge/ s3://REPLACE_KB_BUCKET/REPLACE_KB_PREFIX/ --exclude "*" --include "sop-*.md" --include "faq-*.md" --region ap-southeast-2
```

Do not use `--delete` for the KB source.

## Start ingestion

```bash
aws bedrock-agent start-ingestion-job --knowledge-base-id 9J62RRP7V6 --data-source-id REPLACE_WITH_DATA_SOURCE_ID --region ap-southeast-2
```

Check the returned ingestion job ID, then inspect the job:

```bash
aws bedrock-agent get-ingestion-job --knowledge-base-id 9J62RRP7V6 --data-source-id REPLACE_WITH_DATA_SOURCE_ID --ingestion-job-id REPLACE_WITH_JOB_ID --region ap-southeast-2 --query 'ingestionJob.{status:status,stats:statistics,reasons:failureReasons}' --output json
```

Wait for the status to become `COMPLETE`; inspect failure reasons for `FAILED` or `STOPPED`.

## Retrieval acceptance questions

Use TeamOps AI Knowledge Base search:
- Why does `customer_id,Name,email` fail with SCHEMA_MISMATCH?
- What should I check if I uploaded an object but see no execution record?
- Is a header-only CSV with zero rows considered a success?
- What does `record_count` mean in DynamoDB execution metadata?
- Can I trust a `SUCCEEDED` record as proof of valid customer email addresses?
- Are Related Knowledge Sources exact agent trace citations?

Accept only answers grounded in the new documents. If retrieval is empty, confirm the correct source bucket/prefix, ingestion status, supported Markdown parsing, and KB permissions.

## Caution

Documents are intentionally synthetic. Updating this KB improves the indexed text only; it does not modify the AgentCore Harness configuration, permissions, tool schemas, or deployed website. Knowledge Base ingestion and subsequent retrieval/embedding can incur AWS charges.
