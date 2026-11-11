"""Low-cost synthetic AWS Glue Python shell ETL smoke-test.

Use Job parameters --demo-mode=success or --demo-mode=fail to produce
safe, observable runs for TeamOps AI. No S3 or customer data is accessed.
"""
import argparse
import csv
import io
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("teamops-glue-demo")


def run(mode):
    source = """customer_id,name,email
C001,Alice,alice@example.invalid
C002,Bob,bob@example.invalid
C003,Cora,cora@example.invalid
"""
    rows = list(csv.DictReader(io.StringIO(source)))
    required = {"customer_id", "name", "email"}
    if not required.issubset(rows[0]):
        raise ValueError("SCHEMA_MISMATCH: synthetic source headers invalid")
    logger.info("Synthetic source rows=%d", len(rows))
    transformed = [{"customer_id": row["customer_id"], "name": row["name"].upper(), "email": row["email"]} for row in rows]
    logger.info("Transformation completed: %s", json.dumps({"records": len(transformed)}))
    if mode == "fail":
        raise RuntimeError("DEMO_ETL_VALIDATION_FAILURE: intentional failure for TeamOps AI read-only diagnostics")
    logger.info("ETL_SUCCEEDED rows=%d (no data persisted)", len(transformed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-mode", choices=["success", "fail"], default="success")
    args, _ = parser.parse_known_args()
    logger.info("Starting TeamOps synthetic Glue Python shell job; mode=%s", args.demo_mode)
    run(args.demo_mode)
