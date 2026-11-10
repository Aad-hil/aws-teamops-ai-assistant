# ETL-004 — Bad suffix filter skips data file

**Classification:** RECONSTRUCTED / SYNTHETIC INCIDENT — NOT a real production event  
**Service:** ETL orchestration / Amazon S3 / Step Functions  
**Scenario status:** Example FAILED or DEGRADED; no real execution occurred  
**SOP:** SOP-18 (Missing S3 trigger for ETL workflow)  
**Documentation:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html

## Illustrative log excerpt (not sourced from a real log)
```text
[SIMULATED][UTC time omitted] service=pipeline incident=ETL-004 severity=ERROR
[SIMULATED] message="S3 object uploaded to input/ but no trigger"
[SIMULATED] investigation_note="Example only: no account, job ID, or customer data is represented."
```

## Scenario context
An ETL job or dependency experiences **bad suffix filter skips data file**. This record is meant for similarity retrieval during operator-led investigation, not for claims that the failure occurred in a live system.

## Initial hypothesis
Suffix filter excludes actual file extension. This is a possible cause, not a verified diagnosis.

## Evidence to request from an authorized read-only tool
1. Exact job run, query, Lambda request or workflow execution ID and UTC event time.
2. Compare actual object key and notification suffix.
3. Corresponding service logs and relevant metrics, scoped to the same time window.
4. Source/target counts, object keys and retry history where applicable.

## Proposed RCA procedure
1. Compare observed error signatures with this scenario, checking for contradictory evidence.
2. Follow **SOP-18** and the official linked AWS resource for service-specific checks.
3. Explain confirmed findings separately from suspected causes.
4. Draft a minimally invasive recovery plan; seek authorization for write operations and replay.
5. After approved action, verify execution status and end-to-end data correctness.

## Guardrails
- No live execution metadata, customer data or credentials are included.
- Do not assert that ETL-004 occurred or that the suggested fix was run.
- Never treat this simulated log line as evidence about the user's AWS account.
