import json
import os
import boto3

table = boto3.resource("dynamodb").Table(os.environ["EXECUTIONS_TABLE"])


def lambda_handler(event, context):
    # Internal-only diagnostic function. Caller authentication and team
    # authorization MUST be implemented before attaching to a user-facing agent.
    limit = min(max(int((event or {}).get("limit", 10)), 1), 25)
    # Scan is intentionally for small synthetic demo tables only.
    # Production workloads should use a team/project GSI and Query.
    items = []
    response = table.scan(Limit=100)
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response and len(items) < 500:
        response = table.scan(
            Limit=100, ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))
    items = [
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
    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return {"statusCode": 200, "body": json.dumps({"executions": items[:limit]})}
