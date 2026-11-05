# Customer Ingestion — TeamOps Sample Project

Owner team: data-engineering
Project ID: customer-ingestion

## Architecture
A CSV is uploaded to the S3 input/ prefix. An S3 ObjectCreated event triggers the processor Lambda. The Lambda checks for customer_id, name, and email columns, then writes a copy to processed/ and records execution metadata in DynamoDB. CloudWatch receives logs.

## Operations
Successful runs have status SUCCEEDED in the executions table. Missing required CSV columns produce a FAILED record with SCHEMA_MISMATCH. Use the diagnostics Lambda to inspect recent synthetic executions. This documentation is static and cannot confirm current execution status.

## Security
This project contains only synthetic data. No team member should access resources based solely on a chat prompt. User authentication, team authorization, and audit logging must be enforced by the future assistant backend.
