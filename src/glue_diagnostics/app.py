"""Read-only AWS Glue job-run diagnostics for one deployment-allowlisted job.

This Lambda is intended as an internal AgentCore Gateway Lambda target, not a public API.
A Gateway caller must be authenticated/authorized upstream; IAM additionally scopes
the function role to a single Glue job. No writes or job arguments are exposed.
"""
import logging
import os
import re
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
JOB_NAME = os.environ.get("GLUE_JOB_NAME", "")
ALLOWED_ACTIONS = {"recent_runs", "get_run"}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")
MAX_RETURNED = 10
MAX_ERROR_LENGTH = 600


def _stamp(value):
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _summarize(run):
    # Return only fields useful for RCA. Never expose Arguments, security config,
    # job role, connections, secrets, or raw unbounded exception details.
    return {
        "run_id": run.get("Id"),
        "state": run.get("JobRunState"),
        "started_at": _stamp(run.get("StartedOn")),
        "completed_at": _stamp(run.get("CompletedOn")),
        "duration_seconds": run.get("ExecutionTime"),
        "worker_type": run.get("WorkerType"),
        "number_of_workers": run.get("NumberOfWorkers"),
        "error_message": str(run.get("ErrorMessage") or "")[:MAX_ERROR_LENGTH],
    }


def lambda_handler(event, context):
    if not JOB_NAME:
        return {"error": "Glue diagnostics are not configured"}
    if not isinstance(event, dict):
        return {"error": "Invalid request"}
    args = event.get("arguments", event)
    if not isinstance(args, dict):
        return {"error": "Invalid arguments"}
    if args.get("job_name") not in (None, JOB_NAME):
        return {"error": "Job is not in the deployment allowlist"}
    action = args.get("action", "recent_runs")
    if action not in ALLOWED_ACTIONS:
        return {"error": "Unsupported read-only action"}

    try:
        client = boto3.client("glue")
        if action == "get_run":
            run_id = args.get("run_id")
            if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
                return {"error": "Invalid run_id"}
            response = client.get_job_run(JobName=JOB_NAME, RunId=run_id, PredecessorsIncluded=False)
            return {"job_name": JOB_NAME, "run": _summarize(response["JobRun"]), "evidence": "Live AWS Glue GetJobRun result"}
        limit = args.get("limit", 5)
        if type(limit) is not int or not 1 <= limit <= MAX_RETURNED:
            return {"error": "limit must be an integer between 1 and 10"}
        response = client.get_job_runs(JobName=JOB_NAME, MaxResults=limit)
        runs = [_summarize(x) for x in response.get("JobRuns", [])][:limit]
        return {"job_name": JOB_NAME, "runs": runs, "returned_count": len(runs), "evidence": "Live AWS Glue GetJobRuns result", "note": "This reads only the configured job. It does not inspect Redshift, Step Functions, or CloudWatch logs."}
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        LOG.warning("Glue diagnostics API failed: %s", code)
        return {"error": "Unable to read Glue job runs", "aws_error_code": code}
    except (KeyError, ValueError, TypeError):
        LOG.exception("Unexpected Glue API response")
        return {"error": "Unexpected Glue response"}
