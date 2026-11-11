# Create a synthetic Glue ETL job in the AWS Console

This is an intentionally tiny **AWS Glue Python shell** demonstration, *not* a Spark / PySpark workload. It is designed to provide one SUCCEEDED and one FAILED Glue job run cheaply for the TeamOps AI read-only Glue diagnostics integration. It processes three hard-coded fictitious rows, writes no S3 objects and contains no customer data.

## 1. Create and configure
1. Select ap-southeast-2 (Sydney) in the AWS Glue Studio console → **ETL jobs**.
2. Create a **Python shell script editor** job (not Spark) and paste the script from `samples/glue/teamops_glue_demo.py` into the Script tab.
3. Name it `teamops-glue-demo-etl`.
4. Select a dedicated AWS Glue IAM service role with appropriate Glue script/log bucket access. The role should trust `glue.amazonaws.com`; apply least privilege and do not select an admin role.
5. Prefer the smallest supported Python shell capacity (0.0625 DPU), Python 3.9 if offered, no schedule, one concurrent run, and a small timeout. Avoid unnecessary network connections, crawlers or additional workers.
6. Save, then Run the job with no parameters: by default it produces a **SUCCEEDED** test run.
7. For a controlled failure, add an advanced job parameter `--demo-mode` with value `fail` (console label may say Job parameters / Default arguments) and Run again. The job deliberately throws `DEMO_ETL_VALIDATION_FAILURE`, producing **FAILED**. Restore to `success` afterward. Ensure status is terminal, then stop running it.
8. Compare actual job run IDs, timestamps and statuses in the Glue **Runs** tab. Never assume they exist before execution.

If setting job parameters through the console seems confusing, temporarily change the `default="success"` in `samples/glue/teamops_glue_demo.py` to `default="fail"`, save, run once, and revert. No real records are modified.

## 2. Connect to TeamOps AI Glue diagnostics
- Use `GlueDiagnosticJobName=teamops-glue-demo-etl` when deploying PR #10 SAM changes.
- Add the newly deployed `GlueDiagnosticsFunction` as an authenticated Lambda target of your existing AgentCore Gateway, with tools for `recent_runs` and `get_run`.
- Do not expose the function through API Gateway or unauthenticated Lambda URL.
- The current customer-ingestion diagnostics target is **not** a Glue job diagnostic tool.

## 3. Validation questions
- "List the five most recent runs of the teamops-glue-demo-etl job."
- "What was the status and error for the latest failed run of teamops-glue-demo-etl?"
- "Using real Glue run metadata and the knowledge base, explain why the demo ETL job failed."
- "Show me Redshift live errors." → should say Redshift diagnostics have not yet been integrated.

## Costs
Glue job **runs cost money** even with no persisted output. Check the current AWS Glue pricing for ap-southeast-2, confirm the smallest available Python shell capacity, and use only 1–2 short runs. Do not create an automatic schedule.

## Limitations
This Python shell demo does not reproduce Spark executor OOM errors; it demonstrates live job-run retrieval and safe failure analysis only. A Spark-specific demo can be added later after considering extra compute costs.
