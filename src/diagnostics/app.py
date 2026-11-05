import os
import boto3

table = boto3.resource("dynamodb").Table(os.environ["EXECUTIONS_TABLE"])


def lambda_handler(event, context):
    # Internal-only demo diagnostic function. Enforce caller authentication
    # and team authorization before exposing this tool to end users.
    event = event if isinstance(event, dict) else {}

    try:
        limit = min(max(int(event.get("limit", 10)), 1), 25)
    except (ValueError, TypeError):
        return {"error": "Invalid limit. Provide an integer between 1 and 25."}

    # Scan is only suitable for small synthetic demo tables.
    # Production should use a team/project GSI with Query and pagination.
    items = []
    scan_args = {"Limit": 100}

    while len(items) < 500:
        response = table.scan(**scan_args)
        items.extend(response.get("Items", []))
        if "LastEvaluatedKey" not in response:
            break
        scan_args["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    executions = [
        {
            "execution_id": item["execution_id"],
            "status": item["status"],
            "timestamp": item["timestamp"],
            "source_key": item["source_key"],
            "error": item.get("error", ""),
            "record_count": int(item.get("record_count", 0)),
            "team_id": item.get("team_id", ""),
            "project_id": item.get("project_id", ""),
        }
        for item in items
        if item.get("team_id") == "data-engineering"
        and item.get("project_id") == "customer-ingestion"
    ]
    executions.sort(key=lambda item: item["timestamp"], reverse=True)
    return {"executions": executions[:limit]}
