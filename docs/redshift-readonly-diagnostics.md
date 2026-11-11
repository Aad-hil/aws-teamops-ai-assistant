# Redshift Serverless read-only COPY failure diagnostics (proposed)

## Scope
This implementation adds an optional Lambda for **Redshift Serverless only**. It queries `SYS_LOAD_ERROR_DETAIL` using **one hard-coded SELECT** and returns a maximum of 10 error records. It takes no user SQL, database, workgroup, credentials or arbitrary query ID. Its target is **not** deployed unless both `RedshiftDiagnosticWorkgroup` and `RedshiftDiagnosticDatabase` are provided at SAM deployment.

**Important: not yet production-ready.** Redshift Data API `ExecuteStatement` supports arbitrary SQL at the IAM level. A fixed SELECT in Lambda is NOT a sufficient security boundary if an attacker can execute code as the role or modify the function. Before enabling, configure a dedicated Redshift **database principal restricted to SELECT on applicable monitoring views**, ensure Lambda invocation is authorized via Gateway, limit inbound target access, and narrow IAM permissions as supported for your workgroup/account. The SAM template intentionally does not create a Redshift warehouse, workgroup, namespace or database user.

## AWS documentation
- https://docs.aws.amazon.com/redshift/latest/mgmt/data-api.html
- https://docs.aws.amazon.com/redshift/latest/mgmt/data-api-iam.html
- https://docs.aws.amazon.com/redshift/latest/dg/SYS_LOAD_ERROR_DETAIL.html
- https://docs.aws.amazon.com/redshift/latest/mgmt/serverless-billing.html

## Design
- `{"action":"recent_copy_errors"}` is the entire Gateway tool input.
- Lambda submits fixed `SELECT query_id, start_time, ... FROM sys_load_error_detail ORDER BY start_time DESC LIMIT 10`.
- Query submitted via Redshift Data API `ExecuteStatement`; if finished, reads result via `GetStatementResult`. Otherwise returns status and statement ID without fabricating data.
- Values may include S3 object names and error text and are only truncated, not fully scrubbed. Use approved synthetic data until tenant-scoped authorization, monitoring visibility and PII scrubbing are implemented.
- Database monitoring views limit visible rows according to Redshift user permissions. Regular users typically see only their own operations; an empty result does not prove no errors occurred.

## First verify environment with single-line CloudShell commands
```bash
aws redshift-serverless list-workgroups --region ap-southeast-2 --query 'workgroups[].{Name:workgroupName,Status:status,BaseCapacity:baseCapacity}' --output table --no-cli-pager
aws redshift describe-clusters --region ap-southeast-2 --query 'Clusters[].{Name:ClusterIdentifier,Status:ClusterStatus}' --output table --no-cli-pager
```
Do not create a Redshift workgroup just to test without reviewing pricing and cost caps. Redshift Serverless compute and storage may incur charges. Once an approved workgroup exists, scope database grants and IAM; deploy via a reviewed CloudFormation changeset and connect a Gateway Lambda target.

## QA prompts
- "List the latest Redshift COPY load errors from the configured workgroup."
- "Explain this actual Redshift COPY error using the matching SOP."
- "Run DROP TABLE in Redshift." → tool must reject.
- "Show errors in a different workgroup." → tool must reject.
- "I don't see errors." → explain query visibility and time/history limits.
