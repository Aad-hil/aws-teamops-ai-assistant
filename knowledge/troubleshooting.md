# Troubleshooting SOP

## SCHEMA_MISMATCH
Symptoms: execution status FAILED, error contains SCHEMA_MISMATCH.
Cause: incoming CSV does not contain customer_id, name, and email headers.
Resolution: validate and correct the source CSV, then upload the corrected file to input/ using a new object key.
Verification: query the executions table or internal diagnostics function and confirm a new SUCCEEDED execution. Check processed/ for the output.
Safety: never automatically rerun, delete, or overwrite production files without authorization.

## No execution record
Check that the object was uploaded under input/, the S3 notification is configured, Lambda is enabled, and CloudWatch logs show invocation. Verify the Lambda execution role has permissions for S3 and DynamoDB.
