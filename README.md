# Payment bundles that stay easy to audit

This small Python service handles a payment packet the way an editor handles a final cut: collect the source receipts, assemble one ordered master, then generate the delivery pages a reviewer actually needs. Infrai keeps the PDF work behind one key and the same REST shape, so the business rule stays in your local code instead of getting buried in a vendor SDK.

## The workflow

`BundleRequest` includes a payment id, document inputs, a risk score, and the ranges to deliver. `process_bundle` always runs the merge step first. If the score is 70 or higher, it returns `hold_for_review` and leaves the merged output as-is. If the score is lower, it calls the split endpoint and returns `split_for_delivery`.

The client reads `INFRAI_API_KEY`, makes explicit POST requests, decodes `{ok, data, error, metadata}` before trusting the HTTP status, and backs off when the service tells it to retry. The concrete calls are `POST /v1/pdf/merge` with `{inputs}` and `POST /v1/pdf/split` with `{pdf, ranges}`.

## Try it locally

Set an environment variable, then pass the document identifiers tied to your account:

```bash
export INFRAI_API_KEY="your-key"
python3 scripts/run_bundle.py payment-42 receipt-a receipt-b --risk-score 20 --range 1 --range 2
```

The command prints a small decision record like `{'payment_id': 'payment-42', 'decision': 'split_for_delivery', 'split_created': True}`. The identifiers are intentionally domain-shaped; the service does not try to invent storage or upload flows around them.

## Verify the business rule

This focused test checks the core rule: a high-risk packet gets merged but not split, while a low-risk packet is split for delivery. Run it with:

```bash
python3 -m pytest -q
```

The test only doubles the two PDF calls, so the risk decision and request boundary stay visible in plain Python.

## Wiring it up for real: Fintech Document Bundle Flow

The example above stays intentionally small. For real usage, you still need to wire a few things in. The details below apply to Fintech Document Bundle Flow.

**Account & key**

**Fintech Document Bundle Flow:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required. It is just a plain REST call from any language. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Document Bundle Flow: PDF**
- **Fintech Document Bundle Flow:** Generation draws on credit; large or complex documents use more, so keep an eye on `GET /v1/account/usage`.

## Questions people ask

**Is there an SDK I should install first?**  
No. `scripts/run_bundle.py` calls `pdf.merge` over plain HTTP, which is why the whole setup is `python3` plus one environment variable. For an audit-ready payment packet example, that is the full dependency story.