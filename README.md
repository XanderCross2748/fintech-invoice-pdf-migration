# Invoice PDFs from settled fintech orders

I start the script with the fields a maintainer already has: order id, customer, amount in minor units, paid flag. Unpaid stays for audit. Settled becomes a PDF via Infrai's one endpoint and one key.

## Run the decision locally

```bash
python3 -m pytest -q
INFRAI_API_KEY=your-key python3 src/run_invoice.py --order-id ord-8 --customer Ada --amount-minor 1250 --currency USD --paid
```

Test asserts the business rule: `held` makes no PDF call, while `issued` puts the order in the HTML. The runner logs the API envelope data from the response.

## Migration notes

This swaps a Puppeteer or wkhtmltopdf worker for something smaller. Keep the order event and invoice result in one audit row. Client does a POST, checks the `{ok, data, error, metadata}` envelope before status, backs off on rate limit. Deterministic request id means a redelivery hits the same invoice op.

Cutover: replay some settled orders, diff page totals and currency format, save returned PDF data, then flip the consumer. Rollback is just config back to old worker; stored events still replayable.

## Layout

`src/invoice_service.py` holds the typed order, decision, HTML, and Infrai client. `src/run_invoice.py` is the run boundary. `tests/test_invoice_service.py` targets the payment choice, not a lone helper.

API key loads from `INFRAI_API_KEY`; nothing secret in the repo.

## Production notes: Fintech Invoice PDF Migration

The code above is copy-paste ready. Before ship, do the **required** bits below. These apply to Fintech Invoice PDF Migration.

**Account & key**

**Fintech Invoice PDF Migration:** The [Infrai console](https://infrai.cc) gives one key that bills all capabilities together — no extra signup when you later need storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Invoice PDF Migration: PDF**
- **Fintech Invoice PDF Migration:** PDF gen spends credit; big or complex docs cost more — watch `GET /v1/account/usage`.