from src.day18_adapter import StubRAGAdapter


def test_stub_adapter_returns_expected_shape():
    result = StubRAGAdapter().run_rag("hello")
    assert set(result.keys()) == {"answer", "contexts", "source_ids", "latency_ms"}
    assert isinstance(result["contexts"], list)
