from ledge_lang.sdk import DeterministicAIClient, FakeAIClient, Uncertain


def test_fake_client_returns_uncertain_from_mapping():
    client = FakeAIClient(
        responses={
            "case": {
                "value": "route",
                "confidence": 0.7,
                "source": "fixture",
                "metadata": {"kind": "test"},
            }
        }
    )
    result = client.predict("case")
    assert isinstance(result, Uncertain)
    assert result.value == "route"
    assert result.confidence == 0.7
    assert result.source == "fixture"
    assert result.metadata["kind"] == "test"


def test_deterministic_client_returns_configured_uncertain():
    expected = Uncertain(value="ok", confidence=1.0)
    client = DeterministicAIClient(responses={"case": expected})
    assert client.predict("case") is expected


def test_deterministic_client_missing_case_returns_zero_confidence_uncertain():
    client = DeterministicAIClient(responses={})
    result = client.predict("missing")
    assert result.value is None
    assert result.confidence == 0.0
    assert result.warnings
