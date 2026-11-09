# AgentCore Gateway — synthetic Knowledge Base retrieval

This feature reuses the existing, synced Bedrock Knowledge Base in **ap-southeast-2**. It adds a read-only Lambda with IAM access only to that Knowledge Base. It does **not** create or resync the KB, modify AgentCore Memory, or change the existing diagnostics tool.

## Deploy

Merge this branch first, then from CloudShell:

```bash
git pull origin main
aws bedrock-agent list-knowledge-bases --region ap-southeast-2 --query 'knowledgeBaseSummaries[].{id:knowledgeBaseId,name:name,status:status}' --output table
# Copy the existing knowledge base ID shown above:
export KB_ID=REPLACE_WITH_EXISTING_KB_ID
sam build
sam deploy --stack-name teamops-ai-demo --region ap-southeast-2 --capabilities CAPABILITY_IAM --resolve-s3 --parameter-overrides KnowledgeBaseId="$KB_ID"
```

If your existing stack uses a managed SAM deployment bucket or additional parameters, retain those settings. Review the CloudFormation change set before deploying.

Check output:

```bash
aws cloudformation describe-stacks --stack-name teamops-ai-demo --region ap-southeast-2 --query "Stacks[0].Outputs[?OutputKey=='KnowledgeRetrievalFunctionArn'].OutputValue | [0]" --output text
```

Smoke test the Lambda (the Lambda execution role must be able to retrieve from the KB):

```bash
aws lambda invoke --region ap-southeast-2 --function-name teamops-ai-demo-kb-retrieval --cli-binary-format raw-in-base64-out --payload '{"query":"How do we resolve SCHEMA_MISMATCH?"}' /tmp/kb-result.json
cat /tmp/kb-result.json
```

## Register as a new Gateway Lambda target

In **Bedrock AgentCore → Gateways → teamops-ai-gateway → Add target**, choose **AWS Lambda** and select `teamops-ai-demo-kb-retrieval`. Configure a single tool:

- Tool name: `retrieve_project_knowledge`
- Description: Retrieve synthetic customer-ingestion architecture and troubleshooting documentation. Not a live status lookup.
- Input schema: `{"type":"object","properties":{"query":{"type":"string","description":"Question about project architecture, SOPs, or known errors"}},"required":["query"],"additionalProperties":false}`

Ensure the Gateway target has permission to invoke the Lambda (the console may configure this for you; otherwise configure the Lambda resource policy/target role appropriately). Do not remove the existing diagnostics target.

Test the Gateway tool first, then test in the Harness Playground:

> Find the latest failed customer-ingestion execution using diagnostics, retrieve the matching troubleshooting SOP, and explain how to fix it. Cite the source document.

Verify the agent distinguishes **live execution status** from **synthetic documentation**, does not fabricate missing evidence, and returns a document source when available.

## Security and limitations

- No public Lambda URL or API Gateway endpoint is created.
- Lambda IAM is scoped to the configured KB; user/team authorization must be enforced upstream before exposing the tool to end users.
- Query is capped at 1,000 characters, results at 5, and each excerpt at 1,200 characters.
- S3 source URI may be absent depending on the KB data source.
- The retrieval response contains documentation excerpts, not validated remediation actions.
