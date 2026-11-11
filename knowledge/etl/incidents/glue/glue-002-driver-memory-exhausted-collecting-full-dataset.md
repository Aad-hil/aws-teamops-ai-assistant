# GLUE-002 — Driver memory exhausted collecting full dataset

**Classification:** RECONSTRUCTED / SYNTHETIC INCIDENT — NOT a real production event  
**Service:** AWS Glue  
**Scenario status:** Example FAILED or DEGRADED; no real execution occurred  
**SOP:** SOP-01 (Glue Spark executor OOM)  
**Documentation:** https://docs.aws.amazon.com/glue/latest/dg/monitor-profile-debug-oom-abnormalities.html

## Illustrative log excerpt (not sourced from a real log)
```text
[SIMULATED][UTC time omitted] service=glue incident=GLUE-002 severity=ERROR
[SIMULATED] message="java.lang.OutOfMemoryError: Java heap space at collect()"
[SIMULATED] investigation_note="Example only: no account, job ID, or customer data is represented."
```

## Scenario context
An ETL job or dependency experiences **driver memory exhausted collecting full dataset**. This record is meant for similarity retrieval during operator-led investigation, not for claims that the failure occurred in a live system.

## Initial hypothesis
Large collect() can materialize distributed data on the driver. This is a possible cause, not a verified diagnosis.

## Evidence to request from an authorized read-only tool
1. Exact job run, query, Lambda request or workflow execution ID and UTC event time.
2. Check driver trace for collect/toPandas and replace with distributed operations.
3. Corresponding service logs and relevant metrics, scoped to the same time window.
4. Source/target counts, object keys and retry history where applicable.

## Proposed RCA procedure
1. Compare observed error signatures with this scenario, checking for contradictory evidence.
2. Follow **SOP-01** and the official linked AWS resource for service-specific checks.
3. Explain confirmed findings separately from suspected causes.
4. Draft a minimally invasive recovery plan; seek authorization for write operations and replay.
5. After approved action, verify execution status and end-to-end data correctness.

## Guardrails
- No live execution metadata, customer data or credentials are included.
- Do not assert that GLUE-002 occurred or that the suggested fix was run.
- Never treat this simulated log line as evidence about the user's AWS account.
