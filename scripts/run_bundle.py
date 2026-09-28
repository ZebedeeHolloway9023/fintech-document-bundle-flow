import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.bundle_service import BundleRequest, InfraiPdfClient, process_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge payment documents and optionally split the result.")
    parser.add_argument("payment_id")
    parser.add_argument("inputs", nargs="+", help="Document identifiers accepted by the PDF merge endpoint")
    parser.add_argument("--risk-score", type=int, default=20)
    parser.add_argument("--range", action="append", dest="ranges", default=None)
    args = parser.parse_args()
    request = BundleRequest(args.payment_id, tuple(args.inputs), args.risk_score, tuple(args.ranges or ["1"]))
    result = process_bundle(request, InfraiPdfClient())
    print({"payment_id": request.payment_id, "decision": result.decision, "split_created": result.split is not None})


if __name__ == "__main__":
    main()
