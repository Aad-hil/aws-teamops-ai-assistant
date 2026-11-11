"""Unit tests for scoped read-only Glue diagnostics using stubbed boto3."""
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("glue_diag",Path(__file__).resolve().parents[1]/"src"/"glue_diagnostics"/"app.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_unconfigured_refuses_without_api_call(monkeypatch):
    monkeypatch.delenv("GLUE_JOB_NAME",raising=False)
    monkeypatch.setattr(module,"JOB_NAME","")
    with patch.object(module.boto3,"client") as client:
        assert "error" in module.lambda_handler({"action":"recent_runs"},None)
        client.assert_not_called()


def test_invalid_or_cross_job_request_never_calls_aws(monkeypatch):
    monkeypatch.setattr(module,"JOB_NAME","approved-etl-job")
    with patch.object(module.boto3,"client") as client:
        for event in ({"job_name":"another-job"},{"action":"start_job_run"},{"action":"get_run","run_id":"bad/run"},{"limit":100},{"limit":True}):
            assert "error" in module.lambda_handler(event,None)
        client.assert_not_called()


def test_recent_runs_are_bounded_and_redacted(monkeypatch):
    monkeypatch.setattr(module,"JOB_NAME","approved-etl-job")
    class FakeClient:
        def get_job_runs(self,**kwargs):
            assert kwargs=={"JobName":"approved-etl-job","MaxResults":2}
            return {"JobRuns":[{"Id":"jr_123","JobRunState":"FAILED","StartedOn":datetime(2026,11,11,tzinfo=timezone.utc),"ErrorMessage":"boom","Arguments":{"--password":"secret"},"ExecutionRoleSessionPolicy":"secret"}]}
    with patch.object(module.boto3,"client",return_value=FakeClient()):
        result=module.lambda_handler({"arguments":{"action":"recent_runs","limit":2}},None)
    assert result["runs"][0]["run_id"]=="jr_123"
    assert result["runs"][0]["started_at"]=="2026-11-11T00:00:00+00:00"
    assert "secret" not in str(result)


def test_get_run_only_allowed_job(monkeypatch):
    monkeypatch.setattr(module,"JOB_NAME","approved-etl-job")
    class FakeClient:
        def get_job_run(self,**kwargs):
            assert kwargs=={"JobName":"approved-etl-job","RunId":"jr_123","PredecessorsIncluded":False}
            return {"JobRun":{"Id":"jr_123","JobRunState":"SUCCEEDED"}}
    with patch.object(module.boto3,"client",return_value=FakeClient()):
        assert module.lambda_handler({"action":"get_run","run_id":"jr_123"},None)["run"]["state"]=="SUCCEEDED"
