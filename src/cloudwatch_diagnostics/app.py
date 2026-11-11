"""Read-only, run-scoped CloudWatch logs for the configured Glue Python-shell job.

The Lambda is an INTERNAL Gateway target. Gateway authorization and group enforcement
must precede invocation. The function accepts no log group, account, job name or
arbitrary filter query from the model, and doesn't accept an arbitrary time window.
"""
import logging
import os
import re
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
JOB = os.environ.get("GLUE_JOB_NAME", "").strip()
GROUPS = ("/aws-glue/python-jobs/error", "/aws-glue/python-jobs/output")
RUN_ID_PATTERN = re.compile(r"^jr_[a-fA-F0-9]{16,128}$")
MAX_EVENTS = 20
MAX_BYTES_PER_MESSAGE = 700
MAX_WINDOW = timedelta(hours=24)
REDACT = re.compile(r"(?i)(password|secret|authorization|token|api[_-]?key)\\s*[:=]\\s*([^\\s,;]+)")


def _error(message):
    return {"error": message}


def _timestamp_ms(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp() * 1000)


def lambda_handler(event, context):
    if not JOB:
        return _error("CloudWatch Glue diagnostics are not configured")
    if not isinstance(event, dict):
        return _error("Invalid input")
    args = event.get("arguments", event)
    if not isinstance(args, dict) or set(args) - {"action", "run_id"}:
        return _error("Unsupported input parameters")
    if args.get("action") != "get_run_logs":
        return _error("Unsupported read-only action")
    run_id = args.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        return _error("Invalid Glue run ID")

    try:
        # Verify ownership by the ONE allowlisted job. This is not a generic log reader.
        run = boto3.client("glue").get_job_run(JobName=JOB, RunId=run_id, PredecessorsIncluded=False)["JobRun"]
        if run.get("Id") != run_id:
            return _error("Job run identifier mismatch")
        start = run.get("StartedOn")
        if not isinstance(start, datetime):
            return _error("Glue run start time is unavailable")
        end = run.get("CompletedOn") if isinstance(run.get("CompletedOn"), datetime) else datetime.now(timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        # Restrict requests to a 24-hour window at most.
        query_start = start - timedelta(minutes=2)
        query_end = min(end + timedelta(minutes=2), query_start + MAX_WINDOW)
        if query_end <= query_start:
            return _error("Invalid job run time window")
        client = boto3.client("logs")
        events = []
        missing = []
        truncated = False
        for group in GROUPS:
            # CloudWatch Python-shell streams commonly start with the Glue run ID.
            # Exact prefix prevents accidental retrieval of other jobs' streams.
            params = {
                "logGroupName": group,
                "logStreamNamePrefix": run_id,
                "startTime": _timestamp_ms(query_start),
                "endTime": _timestamp_ms(query_end),
                "limit": MAX_EVENTS,
            }
            try:
                response = client.filter_log_events(**params)
            except client.exceptions.ResourceNotFoundException:
                missing.append(group)
                continue
            for ev in response.get("events", []):
                if not str(ev.get("logStreamName", "")).startswith(run_id):
                    continue
                message = str(ev.get("message", ""))[:MAX_BYTES_PER_MESSAGE]
                message = REDACT.sub(lambda match: match.group(1) + "=[REDACTED]", message)
                events.append({
                    "timestamp_ms": ev.get("timestamp"),
                    "log_group": group,
                    "log_stream": str(ev.get("logStreamName", ""))[:180],
                    "message": message
                })
            if response.get("nextToken"):
                truncated = True
        events = sorted(events, key=lambda x: (x["timestamp_ms"] or 0, x["log_group"]))[-MAX_EVENTS:]
        return {
            "job_name": JOB, "run_id": run_id, "run_state": run.get("JobRunState"),
            "log_events": events, "returned_count": len(events),
            "missing_log_groups": missing,
            "truncated": truncated,
            "evidence": "CloudWatch Logs FilterLogEvents for verified AWS Glue Python-shell run",
            "limitations": "Only the configured Glue job's run-ID-prefixed Python-shell streams; bounded search. Logs may be incomplete or contain sensitive content. No Redshift or Spark logs are queried."
        }
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        LOG.warning("CloudWatch Glue diagnostics failed: %s", error_code)
        return {"error": "Unable to retrieve Glue run logs", "aws_error_code": error_code}
    except (KeyError, ValueError, TypeError):
        LOG.exception("Unexpected log metadata")
        return _error("Unexpected AWS response")
