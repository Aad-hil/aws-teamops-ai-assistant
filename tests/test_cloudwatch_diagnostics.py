"""Mock-only tests for run-scoped CloudWatch log reads."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("cw_app",Path(__file__).resolve().parents[1]/"src"/"cloudwatch_diagnostics"/"app.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_unconfigured_never_calls_aws(monkeypatch):
    monkeypatch.setattr(module,"JOB","")
    with patch.object(module.boto3,"client") as client:
        assert "error" in module.lambda_handler({"action":"get_run_logs","run_id":"jr_"+"a"*32},None)
        client.assert_not_called()


def test_bad_action_and_invalid_run_id_are_rejected(monkeypatch):
    monkeypatch.setattr(module,"JOB","teamops-glue-demo-etl")
    with patch.object(module.boto3,"client") as client:
        for event in ({"action":"get_run_logs","run_id":"jr_foo"},{"action":"delete","run_id":"jr_"+"a"*32},{"action":"get_run_logs","run_id":"jr_"+"a"*32,"log_group":"other"},{"action":"get_run_logs","run_id":"jr_"+"a"*32,"job_name":"other"}):
            assert "error" in module.lambda_handler(event,None)
        client.assert_not_called()


def test_run_correlation_and_redaction(monkeypatch):
    monkeypatch.setattr(module,"JOB","teamops-glue-demo-etl")
    run_id="jr_"+"a"*32
    start=datetime(2026,11,11,10,0,tzinfo=timezone.utc)
    class Glue:
        def get_job_run(self,**kwargs):
            assert kwargs=={"JobName":"teamops-glue-demo-etl","RunId":run_id,"PredecessorsIncluded":False}
            return {"JobRun":{"Id":run_id,"JobRunState":"FAILED","StartedOn":start,"CompletedOn":start+timedelta(minutes=5)}}
    class Logs:
        class exceptions:
            class ResourceNotFoundException(Exception): pass
        def filter_log_events(self,**kwargs):
            assert kwargs["logStreamNamePrefix"]==run_id
            assert kwargs["logGroupName"] in module.GROUPS
            return {"events":[{"timestamp":123,"logStreamName":run_id,"message":"RuntimeError: failure password=abc123"},{"timestamp":124,"logStreamName":"other-run","message":"secret=other"}]}
    with patch.object(module.boto3,"client",side_effect=lambda name: Glue() if name=="glue" else Logs()):
        out=module.lambda_handler({"arguments":{"action":"get_run_logs","run_id":run_id}},None)
    assert out["run_state"]=="FAILED"
    assert out["returned_count"]==2
    assert "abc123" not in str(out)
    assert "other-run" not in str(out)


def test_glue_run_id_mismatch_rejects_log_access(monkeypatch):
    monkeypatch.setattr(module,"JOB","teamops-glue-demo-etl")
    run_id="jr_"+"a"*32
    class Glue:
        def get_job_run(self,**kwargs): return {"JobRun":{"Id":"jr_"+"b"*32,"StartedOn":datetime.now(timezone.utc)}}
    with patch.object(module.boto3,"client",side_effect=lambda name: Glue() if name=="glue" else (_ for _ in ()).throw(AssertionError("unexpected logs client"))):
        assert "error" in module.lambda_handler({"action":"get_run_logs","run_id":run_id},None)
