"""Mocked Redshift diagnostics tests — no warehouse required."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("redshift_diag",Path(__file__).resolve().parents[1]/"src"/"redshift_diagnostics"/"app.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_fail_closed_when_not_configured(monkeypatch):
    monkeypatch.setattr(module,"WORKGROUP","")
    monkeypatch.setattr(module,"DATABASE","")
    with patch.object(module.boto3,"client") as client:
        assert "error" in module.lambda_handler({},None)
        client.assert_not_called()


def test_reject_client_sql_and_workgroup(monkeypatch):
    monkeypatch.setattr(module,"WORKGROUP","teamops-demo")
    monkeypatch.setattr(module,"DATABASE","dev")
    with patch.object(module.boto3,"client") as client:
        for args in ({"action":"run_sql","sql":"DROP TABLE x"},{"action":"recent_copy_errors","sql":"SELECT 1"},{"workgroup":"other"}):
            assert "error" in module.lambda_handler(args,None)
        client.assert_not_called()


def test_fixed_select_and_bounded_output(monkeypatch):
    monkeypatch.setattr(module,"WORKGROUP","teamops-demo")
    monkeypatch.setattr(module,"DATABASE","dev")
    class FakeClient:
        def execute_statement(self,**kw):
            assert kw["Sql"]==module.SQL
            assert kw["WorkgroupName"]=="teamops-demo"
            assert kw["Database"]=="dev"
            return {"Id":"statement-1"}
        def describe_statement(self,**kw):
            return {"Status":"FINISHED"}
        def get_statement_result(self,**kw):
            return {"ColumnMetadata":[{"name":"query_id"},{"name":"error_message"}],"Records":[[{"longValue":42},{"stringValue":"x"*800}]]}
    with patch.object(module.boto3,"client",return_value=FakeClient()):
        out=module.lambda_handler({"arguments":{"action":"recent_copy_errors"}},None)
    assert out["status"]=="FINISHED"
    assert out["errors"][0]["query_id"]==42
    assert len(out["errors"][0]["error_message"])==500


def test_pending_query_does_not_claim_results(monkeypatch):
    monkeypatch.setattr(module,"WORKGROUP","teamops-demo")
    monkeypatch.setattr(module,"DATABASE","dev")
    class FakeClient:
        def execute_statement(self,**kw): return {"Id":"statement-2"}
        def describe_statement(self,**kw): return {"Status":"STARTED"}
        def get_statement_result(self,**kw): raise AssertionError("Must not read pending result")
    with patch.object(module.boto3,"client",return_value=FakeClient()):
        out=module.lambda_handler({"action":"recent_copy_errors"},None)
    assert out["status"]=="STARTED"
    assert "errors" not in out
