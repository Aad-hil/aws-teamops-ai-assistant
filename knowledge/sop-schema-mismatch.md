# SOP: SCHEMA_MISMATCH — Customer Ingestion

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration
Severity: ingestion failure; assess business impact separately

## Signal and scope
The ingestion processor returns a FAILED execution with an error beginning with `SCHEMA_MISMATCH` when an uploaded CSV lacks any header from `customer_id`, `name`, `email`. The current processor checks header names exactly; matching is case-sensitive, and whitespace in headers is not automatically stripped.

## Evidence to collect
1. In TeamOps AI Diagnostics, identify the latest FAILED execution, source_key, UTC timestamp, and execution_id.
2. Confirm the error begins with `SCHEMA_MISMATCH: required columns customer_id,name,email`.
3. With authorized read access, inspect the header row of that specific S3 object, not unrelated files. Do not include customer data or credentials in support messages.
4. Determine which required names are absent or misspelled. Extra columns are permitted.

## Read-only triage
- Required valid header example: `customer_id,name,email`
- Failing examples: `id,name,email`, `customer_id,Name,email`, or `customer_id, name,email` (leading space in the second header).
- A source file may have other content-quality errors that the current code does **not** detect. Do not claim successful ingestion means email addresses, IDs, or all row values were validated.

## Suggested recovery (requires authorized operator)
1. Correct the upstream CSV export to include all three exact required headers.
2. Validate the corrected header and sample rows in a safe environment.
3. After approval, upload the corrected CSV as a **new key** under `input/` so a new S3 ObjectCreated event can be observed.
4. Correlate the new execution with its timestamp and source_key.
5. Confirm status `SUCCEEDED`, check the processed output `processed/<new-execution-id>.csv`, and validate the intended row count.

## Important boundaries
A FAILED result does not necessarily mean no output in every possible system, but this demo writes its processed CSV only after header validation. The processor writes a DynamoDB execution record for handled exceptions. Do not automatically replay, delete, overwrite, or change production files. Use live diagnostics to establish present status: this document is static.
