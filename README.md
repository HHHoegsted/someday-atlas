# Someday Atlas

Someday Atlas is a private homelab app for turning YouTube travel videos into a shared dream map. This MVP lets you save videos manually, create one journey per video, add ordered stops with coordinates, and render those stops as pins connected by journey lines.

## MVP stack

- FastAPI with server-rendered Jinja templates
- SQLite persisted on a Docker volume
- Leaflet with OpenStreetMap tiles
- Docker Compose with a named bridge network for homelab deployment

## Run with Docker

```bash
docker compose up --build
```

The web app will be available at http://localhost:8000.

## Docker topology

- Service: `atlas-web`
- Named network: `someday-atlas-network`
- Persistent volume: `atlas_data` mounted at `/data`

This keeps the app containerized from the start and makes it easy to attach a reverse proxy, backup sidecar, or future services to the same Docker network.

## MVP flows

1. Add a video manually at `/videos/new`
2. Create the single journey for that video
3. Search for a place on the journey page, pick the right hit, and let the helper fill place name, country, region, latitude, and longitude
4. Add or adjust stop details, including optional timestamps
5. Open `/map` to see all routes rendered as pins and lines
6. Use `/capture` on a phone for quick raw notes during a watch session

## API endpoints

- `GET /api/map/journeys`
- `GET /api/journeys/{journey_id}/stops`