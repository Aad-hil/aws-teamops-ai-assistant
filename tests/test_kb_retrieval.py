"""Unit tests with a mocked Bedrock runtime; no AWS credentials required."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("kb_app", Path(__file__).resolve().parents[1] / "src" / "kb_retrieval" / "app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_invalid_query_does_not_call_aws():
    with patch.object(module.boto3, "client") as client:
        assert "error" in module.lambda_handler({"query": ""}, None)
        assert "error" in module.lambda_handler({"query": "x" * 1001}, None)
        client.assert_not_called()


def test_retrieval_response_is_bounded(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_BASE_ID", "ABCDEFGHIJ")
    class FakeClient:
        def retrieve(self, **kwargs):
            assert kwargs["knowledgeBaseId"] == "ABCDEFGHIJ"
            assert kwargs["retrievalConfiguration"]["vectorSearchConfiguration"]["numberOfResults"] == 5
            return {"retrievalResults": [{"content": {"text": "x" * 3000}, "score": 0.8, "location": {"s3Location": {"uri": "s3://demo/knowledge-base/troubleshooting.md"}}}]}
    with patch.object(module.boto3, "client", return_value=FakeClient()):
        result = module.lambda_handler({"arguments": {"query": "SCHEMA_MISMATCH"}}, None)
    assert result["result_count"] == 1
    assert len(result["results"][0]["text"]) == 1200
    assert result["results"][0]["source_uri"].endswith("troubleshooting.md")
