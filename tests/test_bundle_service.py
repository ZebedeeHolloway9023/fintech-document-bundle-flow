from src.bundle_service import BundleRequest, BundleResult, InfraiPdfClient, process_bundle


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def merge(self, inputs):
        self.calls.append(("merge", list(inputs)))
        return {"ok": True, "data": {"pdf": "merged-payment"}}

    def split(self, pdf, ranges):
        self.calls.append(("split", pdf, list(ranges)))
        return {"ok": True, "data": {"pdfs": ["delivery-part"]}}


def test_high_risk_bundle_stays_intact():
    client = FakeClient()
    result = process_bundle(BundleRequest("pay-42", ("receipt-a", "receipt-b"), 80, ("1", "2")), client)
    assert isinstance(result, BundleResult)
    assert result.decision == "hold_for_review"
    assert result.split is None
    assert client.calls == [("merge", ["receipt-a", "receipt-b"])]


def test_low_risk_bundle_is_split_for_delivery():
    client = FakeClient()
    result = process_bundle(BundleRequest("pay-43", ("receipt-a",), 10, ("1",)), client)
    assert result.decision == "split_for_delivery"
    assert result.split is not None
    assert client.calls[-1] == ("split", "merged-payment", ["1"])


def test_split_request_uses_ranges_field():
    client = InfraiPdfClient(api_key="test-key")
    sent = []
    client._post = lambda path, body: sent.append((path, body)) or {"ok": True}
    client.split("merged-payment", ("1-2",))
    assert sent == [("/v1/pdf/split", {"pdf": "merged-payment", "ranges": ["1-2"]})]
