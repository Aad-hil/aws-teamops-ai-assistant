# SOP-06 — Redshift COPY data-format mismatch

**Service:** Amazon Redshift  
**Document type:** Reference-based operational SOP (not a production incident)  
**Risk:** Read-only diagnosis first; human approval for state-changing recovery  
**Source:** https://docs.aws.amazon.com/redshift/latest/dg/SYS_LOAD_ERROR_DETAIL.html

## Detection / symptoms
Typical signal: `Load into table failed: invalid input format`. Similar wording alone does not establish a root cause; correlate job run, query, request, or workflow identifiers.

## Triage (read-only)
1. Identify environment, service, region, job/query/request/execution identifier and UTC time window; confirm permissions.
2. Query SYS_LOAD_ERROR_DETAIL and compare source format, delimiters and COPY settings.
3. Examine actual CloudWatch logs and relevant AWS service metadata; separate observed evidence from hypotheses.
4. Check adjacent upstream/downstream stage outcomes and any prior retry to avoid duplicate side effects.

## Example diagnostic entry point
```text
SELECT query_id, start_time, file_name, error_code, error_message FROM sys_load_error_detail ORDER BY start_time DESC LIMIT 20;
```
Use placeholders only after replacing them with approved resource identifiers. SQL runs in a Redshift query editor; CLI commands run in an authorized terminal. No tool call above has been executed as part of this KB.

## Hypothesis
COPY format options do not match source serialization. Verify against runtime evidence before calling this the root cause.

## Recovery procedure (requires authorization)
1. Establish affected input/output scope, customer impact and idempotency/replay behavior.
2. Fix COPY options or stage corrected input and test in staging.
3. Test in a non-production environment or limited dataset where feasible.
4. Obtain the designated operator's approval before modifying IAM, networking, data, compute capacity, job state, or schedule.
5. Execute through approved operational tooling, capture the change ID, and retain original evidence.

## Verification and rollback
- Confirm a new execution's actual status, job/query ID, error count and outputs.
- Reconcile row counts and business keys; success status alone is insufficient evidence of valid data.
- If recovery fails, stop replays, preserve logs, and restore the previous approved configuration.

## Reference limitations
This is a synthesized troubleshooting procedure based on public AWS documentation; it is not an AWS-authored customer-specific runbook. The linked reference explains relevant service behavior but may not cover every step above.
