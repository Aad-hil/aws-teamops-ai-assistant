import boto3
import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote_plus

s3 = boto3.client("s3")
table = boto3.resource("dynamodb").Table(os.environ["EXECUTIONS_TABLE"])
REQUIRED = {"customer_id", "name", "email"}


def lambda_handler(event, context):
    results = []
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        execution_id = str(uuid.uuid4())
        status, error, count = "SUCCEEDED", "", 0
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            if not REQUIRED.issubset(set(reader.fieldnames or [])):
                raise ValueError("SCHEMA_MISMATCH: required columns customer_id,name,email")
            rows = list(reader)
            count = len(rows)
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            s3.put_object(
                Bucket=bucket,
                Key=f"processed/{execution_id}.csv",
                Body=output.getvalue().encode("utf-8"),
                ContentType="text/csv",
            )
        except Exception as exc:
            status, error = "FAILED", str(exc)[:500]
        item = {
            "execution_id": execution_id,
            "source_key": key,
            "status": status,
            "error": error,
            "record_count": count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "team_id": "data-engineering",
            "project_id": "customer-ingestion",
        }
        table.put_item(Item=item)
        print(json.dumps(item))
        results.append({"execution_id": execution_id, "status": status})
    return {"statusCode": 200, "body": json.dumps(results)}
