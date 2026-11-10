# TeamOps AI Assistant — Capabilities and Boundaries FAQ

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration

## What can the assistant do?
It can answer questions about the synthetic customer ingestion project, search indexed project runbooks, display read-only execution diagnostics through authorized tools, and maintain user-specific chat history.

## What does an execution status mean?
`SUCCEEDED` means the processor completed its implemented CSV read/write path for an S3 event and recorded a success item. `FAILED` means an exception was caught during processing, and an error was recorded if the DynamoDB write succeeded. Neither label independently proves the quality of the customer data.

## Where is processed output stored?
When processing succeeds, the Lambda writes an object under `processed/<execution_id>.csv` in the source data bucket, not in the frontend hosting bucket.

## Does the assistant have the latest execution information?
Only when the answer includes an actual current diagnostics tool result. Indexed knowledge documents describe system behavior and can become outdated. The assistant should be transparent when live diagnostics were not consulted.

## Are Related knowledge sources exact citations?
No. The current chat UI retrieves related Knowledge Base excerpts on demand using the question. They are independently retrieved supporting context, not definitive evidence that the AgentCore Harness used those chunks to form its answer.

## Can the assistant fix issues automatically?
The existing diagnostic and knowledge tools are read-only. Operators must approve any manual upload/replay, production configuration changes, or destructive action using separately authorized workflows.

## Who can use TeamOps AI?
An account must be confirmed and signed in with Cognito, and the user must belong to the `teamops-users` group for authorized chat and dashboard APIs. Email verification and administrator authorization are separate steps.

## How do I validate a suspected fix?
Capture the original execution ID, create a reviewed recovery plan, obtain approval for action, then compare the new execution status and output to the expected result. Do not assume a written plan was executed.
