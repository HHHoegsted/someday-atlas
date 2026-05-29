# Someday Atlas

Someday Atlas is a private homelab app for building a shared travel-dream map around places first. Root locations anchor the atlas, child locations add useful detail, and saved videos act as supporting source material that can be attached to places when needed.

The older video-owned journey flow still exists, but the product direction is now places-first.

## Current model

- Root locations are the main anchors of the atlas.
- Child locations let a place expand into neighborhoods, hotels, ports, stations, and attractions.
- Videos can be linked to places as appearances with optional timestamps.
- Place-owned journeys can be rooted at a location and built from saved locations.
- The map renders both legacy video journeys and the newer place-owned journeys.

## MVP stack

- FastAPI with server-rendered Jinja templates
- SQLite persisted on a Docker volume
- Leaflet with OpenStreetMap tiles
- Docker Compose with a named bridge network for homelab deployment

## Run with Docker

```bash
docker compose up --build
```

The web app will be available at http://localhost:8030.

## Docker topology

- Service: `atlas-web`
- Named network: `someday-atlas-network`
- Persistent volume: `atlas_data` mounted at `/data`
- Reserved host port block: `8030-8039`
- Current host port in use: `8030 -> 8000` inside the container

This keeps the app containerized from the start and makes it easy to attach a reverse proxy, backup sidecar, or future services to the same Docker network.

## Current core flows

1. Create a root location at `/locations`
2. Add child locations beneath that root place
3. Search for a place with the geocoding helper and use it to fill name, country, region, and coordinates
4. Save a video at `/videos/new` when you want source material in the atlas
5. Attach that video to a location from the location detail flow
6. Create a place-owned journey rooted at a saved location
7. Open `/map` to see saved places and rendered route lines
8. Use `/capture` on a phone for quick raw notes during a watch session

## Places-first backbone

The app now has a place-first atlas model alongside the older video-owned journey flow.

- `GET /locations` lists top-level locations and lets you create cities, ports, districts, hotels, attractions, and other location nodes.
- `GET /locations/{location_id}` shows a location, its child locations, and all linked video appearances across that location subtree.
- `POST /locations/{location_id}/children` adds nested locations without forcing you to model every detail upfront.
- `POST /locations/{location_id}/appearances` attaches saved videos and optional timestamps to a location.
- `POST /locations/{location_id}/journeys` creates a place-owned journey rooted at that location.

The atlas supports two route models in parallel.

- The old `video -> journey -> stop` flow still works.
- The preferred place-owned route flow lets you create `LocationJourney` records rooted at a location and add saved locations as ordered route stops.
- The map now renders both legacy video journeys and place-owned journeys from saved locations.

## Root locations matter

If you are extending the app, prefer modeling from root locations outward.

In practice that means:

- add or improve location pages before adding more video-centric entry points
- treat videos as linked evidence, not the main container
- make the frontpage, map, and navigation lead users toward saved places
- keep location creation and browsing lightweight and mobile-friendly where possible

## Container test command

The app image now includes `pytest`, so focused tests can run inside Docker:

```bash
docker compose run --rm atlas-web python -m pytest tests/test_location_service.py tests/test_map_payload_service.py
```

## Main routes

- `GET /`
- `GET /locations`
- `GET /locations/{location_id}`
- `GET /location-journeys/{journey_id}`
- `GET /videos/new`
- `GET /capture`
- `GET /map`

## API endpoints

- `GET /api/map`
- `GET /api/map/journeys`
- `GET /api/journeys/{journey_id}/stops`