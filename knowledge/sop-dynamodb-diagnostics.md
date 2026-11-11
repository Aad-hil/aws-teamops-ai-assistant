# SOP: Understanding Execution Diagnostics and DynamoDB Records

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration

## Execution fields
The processor writes one item to ExecutionsTable for each processed S3 event record, using:
- `execution_id`: generated UUID identifying this attempt.
- `source_key`: original S3 key.
- `status`: `SUCCEEDED` or `FAILED`.
- `error`: exception message truncated to 500 characters, or an empty string.
- `record_count`: number of CSV rows read after valid headers, or zero if parsing failed earlier.
- `timestamp`: UTC ISO 8601 timestamp at execution record creation.
- `team_id`: `data-engineering`.
- `project_id`: `customer-ingestion`.

## Reading dashboard results
The internal diagnostics Lambda scans up to 500 items and then filters for this demo team and project, sorts by timestamp descending, and returns up to the requested limit (maximum 25). A scan does not guarantee this is the complete history in larger tables. The Dashboard UI presents the current response; do not assume a missing entry means an execution never occurred.

## Correlation workflow
1. Use `source_key` and `timestamp` to locate an ingestion attempt.
2. Capture `execution_id` before investigating or discussing the attempt.
3. For FAILED status, inspect `error` and correlate with processor CloudWatch logs using authorized access.
4. For SUCCEEDED status, verify `processed/<execution_id>.csv` if an output check is necessary.

## Failure signatures
- `SCHEMA_MISMATCH`: missing required CSV headers; use schema SOP.
- Text-decoding / parse error: examine input encoding and CSV structure.
- S3 AccessDenied or NoSuchKey: examine object existence and execution role permissions.
- DynamoDB write error: the execution may not be represented in the table, so use Lambda logs and AWS metrics.

## Safety
Diagnostics are read-only. Querying is not a request to replay a file, modify IAM permissions, or delete data. Data shown here is synthetic, and current execution state must be checked with live tools.
