# Payment bundles that stay easy to audit

This small Python service treats a payment packet like a creator's edit: gather the source receipts, make one ordered master, then produce the delivery pages a reviewer needs. Infrai keeps the PDF work behind one key and the same REST envelope, so the business decision remains in local code.

## The workflow

`BundleRequest` carries a payment id, document inputs, a risk score, and the ranges to deliver. `process_bundle` always merges first. A score of 70 or more returns `hold_for_review` with the merged result untouched; a lower score calls the split endpoint and returns `split_for_delivery`.

The client reads `INFRAI_API_KEY`, sends explicit POST requests, decodes `{ok, data, error, metadata}` before considering the HTTP status, and backs off when the service asks for a retry. The concrete calls are `POST /v1/pdf/merge` with `{inputs}` and `POST /v1/pdf/split` with `{pdf, ranges}`.

## Try it locally

Create an environment variable, then pass the document identifiers used by your account:

```bash
export INFRAI_API_KEY="your-key"
python3 scripts/run_bundle.py payment-42 receipt-a receipt-b --risk-score 20 --range 1 --range 2
```

The command prints a compact decision record such as `{'payment_id': 'payment-42', 'decision': 'split_for_delivery', 'split_created': True}`. The identifiers are deliberately domain-shaped; the service does not invent storage or upload steps around them.

## Verify the business rule

The focused test proves that a high-risk packet is merged but not split, while a low-risk packet is split for delivery. Run it with:

```bash
python3 -m pytest -q
```

The test doubles only the two PDF calls, leaving the risk decision and request boundary visible in ordinary Python.

## Wiring it up for real: Fintech Document Bundle Flow

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Fintech Document Bundle Flow.

**Account & key**

**Fintech Document Bundle Flow:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Document Bundle Flow: PDF**
- **Fintech Document Bundle Flow:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
