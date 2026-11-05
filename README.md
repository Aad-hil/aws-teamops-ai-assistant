# TeamOps AI — AWS Team-Aware Assistant

A sample, **synthetic-data** AWS project that a Bedrock assistant can inspect. Phase 1 deploys S3 ingestion, Lambda processing, DynamoDB execution tracking, and a read-only diagnostics Lambda. Later phases add Bedrock Knowledge Bases, agent action groups, authenticated team access, and persistent memory.

## Deploy entirely from AWS CloudShell

Prerequisites: an AWS account with permission to deploy CloudFormation/SAM, create IAM roles, S3, Lambda, DynamoDB, and CloudWatch resources. **Review the template and costs before deploying.** Use a sandbox account, not a production account.

```bash
git clone https://github.com/Aad-hil/aws-teamops-ai-assistant.git
cd aws-teamops-ai-assistant
aws sts get-caller-identity
aws configure get region
sam --version
sam build
sam deploy --guided
```

Suggested stack name: `teamops-ai-demo`; region: `us-east-1`; accept IAM role creation (CAPABILITY_IAM). Keep the generated `samconfig.toml` local. If SAM is unavailable, use a CloudShell environment with AWS SAM CLI installed.

After deployment, get outputs:

```bash
aws cloudformation describe-stacks --stack-name teamops-ai-demo --query 'Stacks[0].Outputs' --output table
```

Set the bucket name from the stack output:

```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name teamops-ai-demo --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue | [0]" --output text)
aws s3 cp samples/customers.csv "s3://$BUCKET/input/customers.csv"
```

Wait a few seconds, then inspect execution records:

```bash
TABLE=$(aws cloudformation describe-stacks --stack-name teamops-ai-demo --query "Stacks[0].Outputs[?OutputKey=='ExecutionsTableName'].OutputValue | [0]" --output text)
aws dynamodb scan --table-name "$TABLE" --limit 10
```

Test a failure:

```bash
aws s3 cp samples/invalid_customers.csv "s3://$BUCKET/input/invalid_customers.csv"
```

The processing Lambda logs failures and writes a FAILED record. A diagnostics Lambda provides a bounded, read-only view of executions, but **it is not a public endpoint and does not authenticate end users**.

## Architecture

S3 `input/` -> S3 event -> `teamops-data-processor` Lambda -> `processed/` objects + DynamoDB execution records + CloudWatch logs.

`teamops-diagnostics` Lambda reads the scoped DynamoDB table and returns recent execution summaries. Later, a Bedrock Agent action group will invoke it through a separate authorization layer.

## Security

- Synthetic sample data only. No customer or office data.
- S3 Block Public Access and default encryption enabled.
- Dedicated least-privilege IAM roles.
- Diagnostics response omits raw payloads and secrets.
- Do **not** expose the diagnostics Lambda directly to untrusted users.
- IAM resource permissions alone do not establish team authorization; the future chatbot must authenticate the user and validate team membership server-side.

## Roadmap

- [x] Phase 1: sample AWS workflow, diagnostic tool, infrastructure as code
- [ ] Phase 2: S3 knowledge documents + Bedrock Knowledge Base (S3 Vectors)
- [ ] Phase 3: Bedrock Agent and RAG
- [ ] Phase 4: authenticated, team-scoped agent tool invocation
- [ ] Phase 5: durable AgentCore Memory integration, user/team namespaces
- [ ] Phase 6: internal chatbot UI and end-to-end authorization tests

## Cleanup

```bash
# Empty the demo bucket first (only if it contains demo data)
aws s3 rm "s3://$BUCKET" --recursive
sam delete --stack-name teamops-ai-demo
```

Check CloudFormation and S3 afterward for remaining resources and charges.
