# CampusCoin

CampusCoin (CPC) is a containerized shared-ledger demo project for a campus-style digital banking system. It combines a simple block-based ledger, a Flask web dashboard, and an LLM-ready command surface so the project can be used for class demos, architecture reviews, and future language-driven transaction flows.

The project is designed around a lightweight distributed-systems idea: multiple clients share access to the same ledger volume, each block stores 5 transactions, and every block is linked with SHA256 metadata to preserve chain integrity.

## Highlights

- 3 Docker client containers share the same ledger storage
- 1 Flask web container exposes a banking-style dashboard on `localhost:5001`
- Every block stores:
  - the SHA256 hash of the previous block
  - the pointer to the next block
- Chain verification rewards the active account with `10 CPC` from `angel`
- File locking is built in to reduce concurrent write conflicts
- The frontend already includes an LLM-ready chat console for future tool calling

## Project Structure

```text
CampusCoin/
|-- app.py
|-- docker-compose.yml
|-- Dockerfile.web
|-- requirements.txt
|-- templates/
|   `-- index.html
|-- shared_storage/
|   |-- ledger_core.py
|   |-- app_transaction.py
|   |-- app_checkMoney.py
|   |-- app_checkLog.py
|   |-- app_checkChain.py
|   `-- *.txt
|-- landing_page.html
`-- PROJECT_HANDOVER_REPORT.md
```

## Core Components

### `shared_storage/ledger_core.py`

This is the ledger engine. It is responsible for:

- locating the storage directory through `STORAGE_PATH`
- creating the genesis block when needed
- appending transactions
- sealing a block when it reaches 5 transactions
- calculating and validating SHA256 chain links
- reading balances and account histories
- guarding writes with a filesystem lock

### `app.py`

This is the Flask backend. It:

- renders the main dashboard
- wraps `ledger_core.py` into JSON APIs
- powers transfers, balance views, activity history, and chain verification
- exposes a placeholder assistant endpoint that can later be connected to an LLM

### `templates/index.html`

This is the current banking dashboard UI. It includes:

- a glassmorphism product-style landing section
- account overview cards
- transfer form
- chain verification controls
- activity feed
- mobile preview
- LLM command console and action preview area

## Ledger Rules

The current ledger implementation follows these rules:

1. Each block is stored as a `.txt` file.
2. Each block can contain up to `5` transactions.
3. Line 1 stores `Sha256 of previous block: ...`
4. Line 2 stores `Next block: ...`
5. When a block becomes full:
   the current block is updated with the next pointer first, then its SHA256 is recalculated, and the new block stores that hash as its previous-block reference.
6. `verify_chain()` checks both:
   - previous-block hash consistency
   - next-pointer consistency
7. If chain verification passes, the system appends a reward transaction from `angel` to the selected account.

## How To Run

### Option 1: Docker Compose

This is the recommended way.

```powershell
docker compose up -d --build
```

After startup:

- web dashboard: `http://localhost:5001`
- shared ledger path inside containers: `/storage`

To stop:

```powershell
docker compose down
```

### Option 2: Run Flask On Host

Install dependencies:

```powershell
pip install -r requirements.txt
```

Then run:

```powershell
python app.py
```

If you run on the host, `ledger_core.py` will use the local `shared_storage` folder unless `STORAGE_PATH` is explicitly set.

## API Overview

### `GET /`

Renders the main dashboard.

### `GET /api/overview?account=b1128015`

Returns dashboard data for an account, including:

- balance
- transaction count
- latest block
- income / expense
- recent transactions
- chain health

### `GET /api/log?account=b1128015&limit=20`

Returns recent transaction history for an account.

### `POST /api/transfer`

Request body:

```json
{
  "sender": "b1128015",
  "receiver": "guest",
  "amount": 15
}
```

Behavior:

- validates sender / receiver / amount
- checks sender balance unless sender is `angel`
- appends the transaction to the active block
- seals a new block when needed

### `POST /api/verify`

Request body:

```json
{
  "account": "b1128015"
}
```

Behavior:

- verifies the full ledger chain
- if valid, appends a `10 CPC` reward from `angel`

### `POST /api/assistant`

Request body:

```json
{
  "account": "b1128015",
  "message": "transfer 12 cpc from b1128015 to guest"
}
```

Current behavior:

- parses natural-language intent
- returns a text reply
- returns an `action_preview` object for UI rendering

This endpoint is the cleanest current bridge for LLM integration.

## LLM Integration Guide

If a junior teammate wants to connect an LLM next, this is the best starting path:

### Step 1: Start from `POST /api/assistant`

`app.py` already has `build_assistant_reply(message, account)`. Right now it uses rule-based parsing, but the endpoint shape is already useful:

- input: `account`, `message`
- output: `reply`, `intent`, `action_preview`

That means an LLM can replace or extend the intent parser without changing the frontend structure too much.

### Step 2: Keep execution separate from interpretation

Recommended flow:

1. user types a natural-language command
2. LLM interprets it into a structured action
3. UI shows an action preview
4. user confirms
5. backend calls `/api/transfer` or `/api/verify`

This is safer than letting the LLM directly execute ledger mutations without confirmation.

### Step 3: Suggested action schema

The project already naturally fits a schema like:

```json
{
  "type": "transfer",
  "sender": "b1128015",
  "receiver": "guest",
  "amount": 12
}
```

Possible types:

- `transfer`
- `verify`
- `balance_lookup`
- `history_lookup`

### Step 4: Best file entry points

If continuing LLM work, start here:

- [app.py](/c:/CampusCoin/app.py:73) for assistant intent logic
- [app.py](/c:/CampusCoin/app.py:229) for the assistant API route
- [templates/index.html](/c:/CampusCoin/templates/index.html:321) for the chat UI
- [templates/index.html](/c:/CampusCoin/templates/index.html:477) for frontend assistant rendering and form submission

## Current Project Status

The project currently includes:

- working shared-ledger logic
- working block sealing behavior
- working SHA256 chain verification
- working angel reward flow
- working Flask dashboard
- working Docker setup
- working assistant placeholder UI

The project is already usable as a polished demo and as a base for future LLM-enabled transaction orchestration.

## Known Limitations

- The clients currently share one mounted storage directory rather than maintaining fully independent replicated ledgers.
- The assistant endpoint is rule-based today and does not yet call a real model.
- The system is intended for coursework and demos, not production banking use.

## Suggested Next Steps

1. Replace the rule-based assistant parser with an LLM plus a structured action schema.
2. Add a confirmation step before executing transfers from natural-language requests.
3. Evolve the shared-volume model into per-node local ledgers plus a sync layer.
4. Add authentication if the demo will be used by multiple real users.

## Notes

- Main demo account: `b1128015`
- Reward issuer / mint account: `angel`
- Web port: `5001`

