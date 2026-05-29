# Someday Atlas - Project Instructions

## Project summary

Someday Atlas is a private homelab app for building a shared travel-dream map around places first.

The core object is no longer the video. The core object is the saved place. Root locations anchor the atlas, child locations add useful specificity, and videos act as supporting source material that can be attached to places when needed.

This is not a serious travel-planning tool. It is a cozy private atlas for travel dreaming.

## Core idea

A root location is the anchor for a region of the atlas.

Child locations let that root place expand into useful detail.

Videos can be linked to locations as appearances.

Journeys can be rooted at locations and connected to saved places in order.

Pins on the map represent saved places.

Lines on the map represent journeys, whether they come from the older video-owned model or the newer place-owned model.

Example:

```text
Root location: Japan
Child locations: Tokyo, Hakone, Kyoto, Nara, Osaka
Place-owned journey: Tokyo -> Hakone -> Kyoto -> Nara -> Osaka
Supporting video: Two Weeks in Japan by Train
```

On the map:

```text
Japan anchors the cluster
Tokyo pin -> Hakone pin -> Kyoto pin -> Nara pin -> Osaka pin
```

Each saved location may contain:

- Name
- Kind such as city, district, hotel, port, attraction, station, or place
- Optional parent location
- Country or region
- Latitude and longitude
- Notes
- Linked videos with optional timestamps
- Place-owned journeys rooted at that location

## Product principles

### Places first

Root locations are key.

When in doubt, model the atlas around places instead of videos.

Videos are useful evidence and source material, but they should not dictate the primary information architecture.

### Keep the capture flow lightweight

The app must not ruin the experience of watching travel videos together.

During TV watching, users should be able to capture a thought from their phones with very little effort.

The ideal interaction is:

```text
Tap -> type a short note -> save
```

Detailed editing, geocoding, route ordering, tagging, and cleanup can happen later.

### Manual first

The first version should use manual entry and simple helpers.

Do not depend on YouTube history, Google Takeout, transcript parsing, AI video parsing, or automatic place extraction for core functionality.

The first version should work when a user manually adds:

- A root location
- Child locations
- A saved video
- A location appearance linking a video to a place
- A place-owned journey
- Optional timestamps and notes

### Make it private and local

This is a homelab project. It should be designed to run locally, preferably behind a private network or VPN.

Everything should work in containers and fit naturally into a Docker network.

Avoid external dependencies unless they add clear value and are easy to replace.

### Avoid productivity stink

This is not a task manager, CRM, itinerary optimizer, or booking system.

The tone of the app should be playful, personal, and low-pressure.

The goal is not to optimize vacations. The goal is to preserve and explore shared travel dreams.

## Current backbone

The current app supports two route models in parallel.

- Legacy: `video -> journey -> stop`
- Current direction: `root location -> child locations / video appearances / place-owned journeys`

New work should prefer the places-first model unless there is a specific reason to maintain or extend the legacy path.

## Current MVP scope

The current usable version should support the following features.

### 1. Create root locations manually

Users can create top-level locations such as cities, islands, ports, regions, or other anchor places.

Each root location should support:

- Name
- Kind
- Country
- Region
- Latitude and longitude
- Optional notes

### 2. Add child locations manually

Users can add nested locations beneath a root location.

Examples:

```text
Japan
  Tokyo
    Shinjuku
    Hotel Gracery
```

This hierarchy should stay lightweight. It is fine to start broad and refine later.

### 3. Link videos to places

Users can save a YouTube video manually and attach it to one or more locations as an appearance.

A video appearance may contain:

- The saved video
- Optional timestamp
- Optional note
- Optional order hint

The video is supporting context for the place, not the container for the entire atlas.

### 4. Create place-owned journeys

Users can create a journey rooted at a location and add saved locations as ordered stops.

The order should reflect the story or route being imagined, not necessarily the optimal real-world path.

### 5. Show places and routes on a map

The map should display saved locations as pins.

The map should render both:

- legacy video-owned journeys
- current place-owned journeys

Clicking a pin should show place information plus any relevant linked source material.

### 6. Keep mobile capture simple

The capture page should remain fast and phone-friendly.

Capture events should be allowed to stay messy until later review.

## Recommended technology

A simple Python-based stack is preferred.

Recommended stack:

- Python
- FastAPI
- SQLite
- SQLModel or SQLAlchemy
- Jinja2 templates
- HTMX for small interactive actions
- Leaflet.js for the map
- OpenStreetMap tiles
- Docker Compose for local hosting

Avoid React unless frontend experimentation is an explicit goal.

## Suggested project structure

```text
someday-atlas/
  app/
    main.py
    database.py
    models.py
    routers/
      web.py
      api.py
    services/
      geocoding_service.py
      location_service.py
      map_payload_service.py
      youtube_url_service.py
    templates/
      base.html
      index.html
      locations_index.html
      location_detail.html
      location_edit.html
      location_child_new.html
      location_appearance_new.html
      location_journey_new.html
      location_journey_detail.html
      map.html
      capture.html
      videos_new.html
      video_detail.html
      journey_detail.html
    static/
      app.css
      map.js
  docs/
  tests/
  docker-compose.yml
  README.md
  .github/
    copilot-instructions.md
```

## Suggested data model

### locations

Stores the main atlas entities.

Fields:

```text
id
name
kind
parent_location_id
country
region
latitude
longitude
notes
created_at
updated_at
```

### video_location_appearances

Stores links between saved videos and saved locations.

Fields:

```text
id
video_id
location_id
timestamp_seconds
order_index
note
created_at
updated_at
```

### location_journeys

Stores journeys rooted at a location.

Fields:

```text
id
root_location_id
name
description
created_at
updated_at
```

### location_journey_stops

Stores ordered saved-location stops inside a place-owned journey.

Fields:

```text
id
journey_id
location_id
order_index
note
created_at
updated_at
```

### videos

Stores manually added YouTube videos.

Fields:

```text
id
youtube_url
youtube_id
title
channel_name
notes
created_at
updated_at
```

### Legacy compatibility tables

The legacy `journeys` and `stops` tables still exist and still render on the map.

They should be treated as compatibility paths during the transition rather than the preferred backbone for new product thinking.

## Important routes

### Web routes

```text
GET  /
GET  /locations
POST /locations
GET  /locations/{location_id}
GET  /locations/{location_id}/edit
POST /locations/{location_id}/edit
GET  /locations/{location_id}/children/new
POST /locations/{location_id}/children
GET  /locations/{location_id}/appearances/new
POST /locations/{location_id}/appearances
GET  /locations/{location_id}/journeys/new
POST /locations/{location_id}/journeys
GET  /location-journeys/{journey_id}
POST /location-journeys/{journey_id}/stops
GET  /videos/new
POST /videos
GET  /videos/{video_id}
GET  /capture
POST /capture
GET  /map
```

### API routes

```text
GET /api/map
GET /api/map/journeys
GET /api/journeys/{journey_id}/stops
```

The map API should return a combined payload that can represent:

- saved locations
- legacy video journeys
- place-owned journeys

## Mobile capture mode

Mobile capture is important because the app is likely to be used while watching YouTube on a TV.

Capture should stay deliberately lightweight.

### Capture event concept

A capture event is a quick note created by someone while watching something.

It should not need to be fully structured at the moment it is created.

Example capture events:

```text
HH: Osaka food chaos yes
SO: too crowded
HH: Nara deer situation
SO: that train station looked cozy
```

A capture event can later be processed into:

- A root location idea
- A child location
- A note on a location
- A linked video appearance
- A tag or vote later
- Nothing, if it was just noise

### Suggested capture event fields

```text
id
created_at
created_by
kind
raw_text
processed_at
```

Possible kinds:

```text
place
wow
food
nope
stay
move
note
```

### Design principle

Do not require explicit watch sessions.

Capture events should simply exist as timestamped observations that can be sorted out later.

## Future versions

### Better reconciliation between videos and places

A future version may import YouTube watch history from Google Takeout and suggest likely matches between capture events and saved videos.

This should always be reviewable by the user.

Do not silently attach capture events to videos or places without a correction path.

### Automatic metadata enrichment

A future version may use the YouTube Data API only for metadata enrichment, such as:

- Video title
- Channel name
- Thumbnail
- Duration

The app should not require YouTube API access for core functionality.

### Better geocoding and image support

The app may expand its place-name geocoding helpers and later support uploaded per-place images.

Manual coordinates and local fallback imagery should remain valid.

### Capture clustering

A future version may group capture events by time proximity and suggest likely place or video relationships.

### Couple voting

A future version may allow multiple people to vote on destinations, neighborhoods, hotels, or stops.

### Dream trip generation

A future version may generate fantasy trips from saved places using rules, tags, and votes.

No AI is required.

### AI video parsing

AI video parsing is explicitly out of scope for normal development.

Treat this as a lottery-win feature only.

## Non-goals

Do not build these for the MVP:

- AI video parsing
- Transcript parsing
- Automatic place extraction
- Flight search
- Booking integrations
- Budget planning
- Multi-user account system
- Public sharing
- Full travel itinerary planning
- Complex recommendation engine
- 3D globe rendering

## Current demo target

The current app should be able to do this:

```text
1. Create a root location manually.
2. Add child locations under it.
3. Save a YouTube video manually.
4. Attach that video to one or more saved places.
5. Create a place-owned journey rooted at a location.
6. Open the map and see saved locations plus rendered route lines.
```

A good current demo looks like this:

```text
Root location: Japan
Child locations: Tokyo, Hakone, Kyoto, Nara, Osaka
Supporting video: Two Weeks in Japan by Train
Place-owned journey: Tokyo -> Hakone -> Kyoto -> Nara -> Osaka
Map: saved places as pins, route as a line, source video linked from relevant places
```

## Guiding sentence

Someday Atlas is a private map of places discovered while travel-dreaming, where root locations anchor the atlas, pins hold memories, and journeys connect the places that matter.
