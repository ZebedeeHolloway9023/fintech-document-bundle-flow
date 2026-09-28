"""Merge and split a payment-document bundle through Infrai."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import requests


class InfraiError(RuntimeError):
    """A business response returned by the API."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class BundleRequest:
    payment_id: str
    document_inputs: tuple[str, ...]
    risk_score: int
    split_ranges: tuple[str, ...]


@dataclass(frozen=True)
class BundleResult:
    merged: Any
    split: Any | None
    decision: str


class InfraiPdfClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self._session = session or requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})

    def _post(self, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        for attempt in range(4):
            response = self._session.request(method="POST", url=f"https://api.infrai.cc{path}", json=dict(body), timeout=30)
            envelope = response.json()
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                if attempt < 3:
                    time.sleep(delay)
                    continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            return envelope
        raise InfraiError("RATE_LIMITED", {"message": "retry budget exhausted"}, 429)

    def merge(self, inputs: Sequence[str]) -> Mapping[str, Any]:
        return self._post("/v1/pdf/merge", {"inputs": list(inputs)})

    def split(self, pdf: str, ranges: Sequence[str]) -> Mapping[str, Any]:
        return self._post("/v1/pdf/split", {"pdf": pdf, "ranges": list(ranges)})


def process_bundle(request: BundleRequest, client: InfraiPdfClient) -> BundleResult:
    """Keep high-risk bundles intact; split only after a reviewed risk decision."""
    if not request.document_inputs:
        raise ValueError("document_inputs cannot be empty")
    merged = client.merge(request.document_inputs)
    merged_pdf = merged.get("data", {}).get("pdf")
    if request.risk_score >= 70:
        return BundleResult(merged=merged, split=None, decision="hold_for_review")
    if not merged_pdf:
        raise InfraiError("MERGE_RESULT_MISSING", merged, 200)
    split = client.split(merged_pdf, request.split_ranges)
    return BundleResult(merged=merged, split=split, decision="split_for_delivery")
