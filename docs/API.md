# API

Run the service with:

```bash
uvicorn ai_civilization.api:app --host 127.0.0.1 --port 8000
```

Swagger UI is available at `/docs`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/games` | Create a new civilization |
| GET | `/games/{game_id}` | Read current state |
| POST | `/games/{game_id}/advance` | Advance 1–1000 turns |
| POST | `/games/{game_id}/goals` | Add/replace a directive |
| POST | `/games/{game_id}/train` | Reinforce an adviser preference |
| POST | `/games/{game_id}/reward` | Reward the adviser |
| POST | `/games/{game_id}/punish` | Punish the adviser |
| POST | `/games/{game_id}/disagree` | Reject its last recommendation |
| POST | `/games/{game_id}/replace` | Replace the government AI |
| GET | `/games/{game_id}/history` | Read recent events |

## Example

Create:

```bash
curl -X POST http://127.0.0.1:8000/games \
  -H 'content-type: application/json' \
  -d '{"name":"Aurora","seed":42}'
```

Set a directive:

```bash
curl -X POST http://127.0.0.1:8000/games/GAME_ID/goals \
  -H 'content-type: application/json' \
  -d '{"key":"richest","title":"Become the richest nation","weight":5}'
```

Advance:

```bash
curl -X POST http://127.0.0.1:8000/games/GAME_ID/advance \
  -H 'content-type: application/json' \
  -d '{"turns":10}'
```
