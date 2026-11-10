# SOP: Uploaded CSV Has No Execution Record

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration

## Symptom
An operator uploaded a CSV but cannot find a corresponding record in TeamOps AI Diagnostics.

## Flow to inspect
Expected configured pipeline: S3 object under `input/` -> S3 ObjectCreated notification -> processor Lambda -> DynamoDB execution metadata and, for successful processing, S3 `processed/` output.

## Investigation
1. Confirm the correct S3 data bucket, object key, upload time, and AWS region.
2. Confirm the object was uploaded under `input/`. Files outside the notification's configured prefix may not trigger processing.
3. Inspect the S3 event notification configuration and whether it targets the intended processor Lambda. The SAM template creates the processor; verify notification wiring in the actual deployed bucket.
4. Check whether Lambda invocation metrics and CloudWatch log streams show an invocation near the upload time.
5. Check S3-to-Lambda resource-based invoke permissions and Lambda execution-role permissions for `s3:GetObject`, `s3:PutObject`, and DynamoDB writes.
6. Check for Lambda exceptions, concurrency throttles, or failed event delivery.
7. Inspect the DynamoDB ExecutionsTable directly if authorized, because the demo diagnostics function uses a bounded table scan and is not a complete audit log.

## Interpretation
- No Lambda invocation: prioritize bucket/key/notification/permission checks.
- Lambda invoked, no recorded execution: inspect unhandled exceptions, input event format, and DynamoDB write failures.
- Execution exists in DynamoDB but not Diagnostics: the dashboard filters to `team_id=data-engineering` and `project_id=customer-ingestion`, and limits recent records.
- Status `FAILED`: inspect error details and follow the relevant failure SOP.

## Recovery
Only after human approval, correct the specific configuration or retry with a uniquely named test object. Do not silently trigger production retries. Verify the new invocation, DynamoDB record, and status with live telemetry.
