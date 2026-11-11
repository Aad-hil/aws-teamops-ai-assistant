"""Read-only Redshift Serverless COPY diagnostic lookup.

No caller-provided SQL, workgroup or database identifiers are accepted. ExecuteStatement
runs a single hard-coded SELECT. This Lambda MUST run as a database principal with
SELECT-only privileges; IAM alone cannot make ExecuteStatement read-only.
"""
import logging
import os

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
WORKGROUP = os.environ.get("REDSHIFT_WORKGROUP", "").strip()
DATABASE = os.environ.get("REDSHIFT_DATABASE", "").strip()
MAX_RESULTS = 10
ALLOWED = {"recent_copy_errors"}
SQL = """SELECT query_id, start_time, trim(file_name) AS file_name,
trim(column_name) AS column_name, error_code, trim(error_message) AS error_message
FROM sys_load_error_detail ORDER BY start_time DESC LIMIT 10"""


def _cell(value):
    # Redshift Data API field is a tagged union.
    for key in ("stringValue", "longValue", "doubleValue", "booleanValue"):
        if key in value:
            return value[key]
    return None


def _rows(response):
    names = [x["name"] for x in response.get("ColumnMetadata", [])]
    result = []
    for record in response.get("Records", [])[:MAX_RESULTS]:
        row = {name: _cell(value) for name, value in zip(names, record)}
        # Potentially sensitive file paths and database error text must remain
        # bounded. Restrict usage to approved synthetic/demo data.
        if row.get("file_name") is not None:
            row["file_name"] = str(row["file_name"])[:240]
        if row.get("error_message") is not None:
            row["error_message"] = str(row["error_message"])[:500]
        result.append(row)
    return result


def lambda_handler(event, context):
    if not WORKGROUP or not DATABASE:
        return {"error": "Redshift diagnostics are not configured"}
    if not isinstance(event, dict):
        return {"error": "Invalid request"}
    args = event.get("arguments", event)
    if not isinstance(args, dict) or args.get("action", "recent_copy_errors") not in ALLOWED:
        return {"error": "Unsupported read-only action"}
    # Reject unrecognized client parameters rather than using them as SQL.
    if set(args) - {"action"}:
        return {"error": "Unsupported parameters"}
    try:
        client = boto3.client("redshift-data")
        execution = client.execute_statement(
            WorkgroupName=WORKGROUP, Database=DATABASE, Sql=SQL,
            StatementName="teamops-readonly-copy-errors", WaitTimeSeconds=10
        )
        statement_id = execution["Id"]
        status = client.describe_statement(Id=statement_id)
        if status.get("Status") != "FINISHED":
            return {
                "workgroup": WORKGROUP, "database": DATABASE,
                "statement_id": statement_id,
                "status": status.get("Status", "UNKNOWN"),
                "note": "Diagnostic SELECT is not finished. Inspect this statement via an authorized operator; no result claimed."
            }
        result = client.get_statement_result(Id=statement_id)
        rows = _rows(result)
        return {
            "workgroup": WORKGROUP, "database": DATABASE,
            "statement_id": statement_id, "status": "FINISHED",
            "errors": rows, "returned_count": len(rows),
            "evidence": "Live Redshift Serverless SYS_LOAD_ERROR_DETAIL via fixed SELECT",
            "limitations": "Results depend on database permissions/visibility; no errors returned does not prove no COPY failures occurred."
        }
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        LOG.warning("Redshift Data API diagnostics failed: %s", code)
        return {"error": "Unable to retrieve Redshift load errors", "aws_error_code": code}
    except (KeyError, TypeError, ValueError):
        LOG.exception("Unexpected Redshift Data API response")
        return {"error": "Unexpected Redshift response"}
