import argparse
import json

from invoice_service import InfraiPdfClient, Order, generate_invoice


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue an invoice PDF for a settled order")
    parser.add_argument("--order-id", required=True)
    parser.add_argument("--customer", required=True)
    parser.add_argument("--amount-minor", type=int, required=True)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--paid", action="store_true")
    args = parser.parse_args()
    result = generate_invoice(Order(args.order_id, args.customer, args.currency, args.amount_minor, args.paid), InfraiPdfClient())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
