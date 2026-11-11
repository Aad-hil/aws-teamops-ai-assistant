# GLUE-010 — Glue KMS decrypt denied

**Classification:** RECONSTRUCTED / SYNTHETIC INCIDENT — NOT a real production event  
**Service:** AWS Glue  
**Scenario status:** Example FAILED or DEGRADED; no real execution occurred  
**SOP:** SOP-05 (Glue cannot access S3 source)  
**Documentation:** https://docs.aws.amazon.com/glue/latest/dg/glue-troubleshooting-errors.html

## Illustrative log excerpt (not sourced from a real log)
```text
[SIMULATED][UTC time omitted] service=glue incident=GLUE-010 severity=ERROR
[SIMULATED] message="AccessDeniedException: kms:Decrypt"
[SIMULATED] investigation_note="Example only: no account, job ID, or customer data is represented."
```

## Scenario context
An ETL job or dependency experiences **glue kms decrypt denied**. This record is meant for similarity retrieval during operator-led investigation, not for claims that the failure occurred in a live system.

## Initial hypothesis
Encrypted source needs grant and key policy access. This is a possible cause, not a verified diagnosis.

## Evidence to request from an authorized read-only tool
1. Exact job run, query, Lambda request or workflow execution ID and UTC event time.
2. Inspect encryption key and role's KMS permissions.
3. Corresponding service logs and relevant metrics, scoped to the same time window.
4. Source/target counts, object keys and retry history where applicable.

## Proposed RCA procedure
1. Compare observed error signatures with this scenario, checking for contradictory evidence.
2. Follow **SOP-05** and the official linked AWS resource for service-specific checks.
3. Explain confirmed findings separately from suspected causes.
4. Draft a minimally invasive recovery plan; seek authorization for write operations and replay.
5. After approved action, verify execution status and end-to-end data correctness.

## Guardrails
- No live execution metadata, customer data or credentials are included.
- Do not assert that GLUE-010 occurred or that the suggested fix was run.
- Never treat this simulated log line as evidence about the user's AWS account.
