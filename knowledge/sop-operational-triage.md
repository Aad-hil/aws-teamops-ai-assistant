# Runbook: Customer Ingestion Incident Triage and Escalation

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration

## Purpose
Provide a consistent, evidence-first response when an operator asks the assistant why a customer CSV ingestion failed.

## Triage sequence
1. **Identify the incident.** Obtain the project, time window, source key, and execution ID if supplied.
2. **Get current evidence.** Use live diagnostics for status, timestamp, error, row count, and source key. If current data is unavailable, say so rather than treating a knowledge document as live telemetry.
3. **Classify the failure.**
   - `SCHEMA_MISMATCH`: required header missing.
   - No execution: inspect S3 trigger and Lambda invocation path.
   - Decode/CSV write failure: inspect encoding, row shape, and parser error.
   - Permission failure: inspect S3/DynamoDB/Lambda IAM and CloudWatch logs.
4. **Retrieve applicable SOP.** Match the documented failure class; clearly separate documented guidance from observed runtime evidence.
5. **Propose a safe recovery plan.** Explain expected effect, preconditions, owner, validation step, and rollback/escalation path.
6. **Escalate when required.** Ask an authorized human to review retries, data overwrites, resource-policy changes, deletions, or any action affecting production systems.

## Answer format for the assistant
- Observed status and execution identifier (only if returned by a live authorized tool).
- Evidence and source of evidence, with uncertainties.
- Probable cause, explicitly labeled as a hypothesis if not verified.
- Suggested next checks and least-risk remediation.
- Approval requirement and post-change verification.

## Unsupported assumptions
Do not invent live executions, severity levels, root-cause certainty, runtime logs, customer records, or successful recovery. The synthetic processor does not make autonomous recovery decisions or enforce business-grade data quality.

## Escalation criteria
Escalate immediately for suspected sensitive-data exposure, widespread event delivery failure, recurring access-denied errors, or changes outside documented permissions. Do not use this generic guide as an authorization to operate a real customer production account.
