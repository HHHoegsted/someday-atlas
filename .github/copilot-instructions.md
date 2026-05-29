# Someday Atlas - Project Instructions

## Project summary

Someday Atlas is a private homelab application for turning YouTube travel videos into a shared travel-dream map.

The app is designed for people who watch travel videos together on a TV and want to casually capture places, moments, and ideas from those videos using their phones. Over time, the captured places become pins on a map. Videos can become journeys, where multiple pins are connected with lines in the order they appear in the video.

This is not a serious travel-planning tool. It is a cozy private atlas for travel dreaming.

## Core idea

A YouTube travel video can be represented as a journey.

A journey contains stops.

A stop is a place shown or mentioned in the video.

Stops are shown as pins on a map.

Stops from the same journey are connected with lines.

Example:

```text
Video: Two Weeks in Japan by Train
Journey: Tokyo -> Hakone -> Kyoto -> Nara -> Osaka
```

On the map:

```text
Tokyo pin -> Hakone pin -> Kyoto pin -> Nara pin -> Osaka pin
```

Each stop may contain:

- Place name
- Country or region
- Latitude and longitude
- Optional YouTube timestamp
- Notes
- Tags
- Vote or interest rating
- Link back to the YouTube video

## Product principles

### Keep the capture flow lightweight

The app must not ruin the experience of watching travel videos together.

During TV watching, users should be able to capture a thought from their phones with very little effort.

The ideal interaction is:

```text
Tap -> type a short note -> save
```

Detailed editing, geocoding, route ordering, tagging, and cleanup can happen later.

### Manual first

The first version should use manual video entry.

Do not depend on YouTube history, Google Takeout, transcript parsing, AI video parsing, or automatic place extraction for the MVP.

The first version should work when a user manually adds:

- YouTube URL
- Video title
- Journey name
- Stops
- Notes
- Optional timestamps

### Make it private and local

This is a homelab project. It should be designed to run locally, preferably behind a private network or VPN.

Avoid external dependencies unless they add clear value and are easy to replace.

### Avoid productivity stink

This is not a task manager, CRM, itinerary optimizer, or booking system.

The tone of the app should be playful, personal, and low-pressure.

The goal is not to optimize vacations. The goal is to preserve and explore shared travel dreams.

## MVP scope

The first usable version should support the following features.

### 1. Add a video manually

Users can create a video record with:

- YouTube URL
- Title
- Channel name, optional
- Notes, optional

The app should extract the YouTube video ID from the URL when possible.

### 2. Create a journey for a video

For the MVP, each video can have one journey.

A journey should have:

- Name
- Description, optional
- Associated video

Example:

```text
Journey name: Japan by Train
Video: Two Weeks in Japan by Train
```

### 3. Add stops manually

Users can add stops to a journey.

A stop should have:

- Place name
- Latitude
- Longitude
- Order index
- Optional timestamp
- Optional note

Coordinates can be entered manually in the first version.

A later version may add geocoding by place name.

### 4. Show pins on a map

The map should display all stops as pins.

Clicking a pin should show:

- Place name
- Journey name
- Video title
- Note
- Timestamp, if available
- Link to the YouTube video

### 5. Connect journey stops with lines

Stops from the same journey should be connected by a line in `order_index` order.

The line represents the story or route of the video, not necessarily the optimal travel route.

If a video jumps from Tokyo to Kyoto and then back to Tokyo, the map should show exactly that order.

### 6. Open YouTube at timestamp

If a stop has a timestamp, the app should generate a YouTube timestamp link.

Example:

```text
https://www.youtube.com/watch?v=<video_id>&t=1930s
```

If no timestamp is provided, the app should link to the normal video URL.

## Recommended MVP technology

A simple Python-based stack is preferred.

Recommended stack:

- Python 3.10.12
- FastAPI
- SQLite
- SQLModel or SQLAlchemy
- Jinja2 templates
- HTMX for small interactive actions
- Leaflet.js for the map
- OpenStreetMap tiles
- Docker Compose for local hosting

Avoid React for the first version unless frontend practice is an explicit goal.

The app should be easy to run locally.

## Suggested project structure

```text
someday_atlas/
  app/
    main.py
    database.py
    models.py
    routers/
      videos.py
      journeys.py
      stops.py
      map.py
    services/
      youtube_url_service.py
      map_payload_service.py
    templates/
      base.html
      index.html
      videos_new.html
      journey_detail.html
      map.html
    static/
      app.css
      map.js
  tests/
  docker-compose.yml
  README.md
```

## Suggested database model

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

### journeys

Stores a journey associated with a video.

Fields:

```text
id
video_id
name
description
created_at
updated_at
```

### stops

Stores mapped stops for a journey.

Fields:

```text
id
journey_id
place_name
country
region
latitude
longitude
order_index
timestamp_seconds
note
created_at
updated_at
```

### tags

Optional for the first version, but useful soon after.

Fields:

```text
id
name
```

Example tags:

```text
food
train-friendly
old-town
cozy
nature
beach
mountains
luxury
low-stress
crowded
too-hot
walking-heavy
lottery-only
actually-possible
```

### stop_tags

Optional many-to-many table between stops and tags.

Fields:

```text
stop_id
tag_id
```

### votes

Optional for a later version.

Fields:

```text
id
stop_id
voter_name
rating
note
created_at
```

Possible ratings:

```text
must_go
would_go
maybe
lottery_only
nope
```

## Important routes

### Web routes

```text
GET  /
GET  /map
GET  /videos/new
POST /videos
GET  /videos/{video_id}
GET  /journeys/{journey_id}
POST /journeys
POST /journeys/{journey_id}/stops
```

### API routes

```text
GET /api/map/journeys
GET /api/journeys/{journey_id}/stops
```

The map API should return journey data in a shape that is easy for Leaflet to render.

Example:

```json
{
  "journeys": [
    {
      "id": 1,
      "name": "Japan by Train",
      "video_title": "Two Weeks in Japan by Train",
      "youtube_url": "https://www.youtube.com/watch?v=abc123",
      "stops": [
        {
          "id": 1,
          "place_name": "Tokyo",
          "latitude": 35.6762,
          "longitude": 139.6503,
          "order_index": 1,
          "timestamp_seconds": 200,
          "note": "Food alleys looked amazing"
        },
        {
          "id": 2,
          "place_name": "Kyoto",
          "latitude": 35.0116,
          "longitude": 135.7681,
          "order_index": 2,
          "timestamp_seconds": 1930,
          "note": "Old streets and temples"
        }
      ]
    }
  ]
}
```

## Mobile capture mode

Mobile capture is important because the app is likely to be used while watching YouTube on a TV.

However, the very first MVP can start with manual video and stop entry.

The next step should be a simple phone-friendly capture page.

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

- A stop
- A note on a stop
- A tag
- A vote
- A warning or nope moment
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

Instead, capture events should simply exist as timestamped observations.

Later, the app can group events that happened around the same time.

## Future versions

### Google Takeout import

A future version should support importing YouTube watch history from Google Takeout.

This would allow the app to infer which videos were watched around the same time as phone capture events.

The idea:

```text
Phone capture event:
20:17 - "Osaka food market looked amazing"

Google Takeout watch history:
20:02 - watched "Japan by Train - 14 Days"

Someday Atlas inference:
The note probably belongs to that video.
```

This should be treated as batch reconciliation, not live sync.

The app should allow a user to upload or place a Google Takeout export file into an import folder, then parse YouTube watch history from it.

Possible workflow:

```text
1. User exports YouTube history from Google Takeout.
2. User uploads or copies the export into Someday Atlas.
3. App imports watch history items.
4. App compares watch times with capture events.
5. App suggests likely video matches.
6. User confirms or corrects the matches.
```

Suggested future table:

```text
watch_history_items
  id
  watched_at
  youtube_id
  title
  channel_name
  source
  imported_at
```

Possible matching rule:

```text
For each capture event, find the most recent watched video before the capture time within a configurable time window.
```

Suggested initial matching window:

```text
2 hours
```

The matching result should always be reviewable by the user.

Do not silently attach capture events to videos without a way to correct them.

### Automatic metadata enrichment

A future version may use the YouTube Data API only for metadata enrichment, such as:

- Video title
- Channel name
- Thumbnail
- Duration

The app should not require YouTube API access for core functionality.

### Geocoding

A future version may support place-name geocoding.

Example:

```text
Kyoto, Japan -> latitude and longitude
```

The app should keep manual coordinate entry as a fallback.

### Capture clustering

A future version may group capture events by time proximity.

Example rule:

```text
If two capture events happen within 45 minutes of each other, suggest that they belong to the same cluster.
```

Clusters should be editable.

Users should be able to:

- Merge clusters
- Split clusters
- Move events between clusters
- Attach a cluster to a video
- Leave a cluster unassigned

### Couple voting

A future version may allow multiple people to vote on destinations or stops.

Example:

```text
HH: must_go
SO: would_go
```

The map could later filter by:

- Both like it
- One person likes it
- Lottery only
- Nope
- Actually possible

### Dream trip generation

A future version may generate fantasy trips from saved places.

Possible modes:

```text
Cozy rainy train trip
Food and old towns
Lottery luxury
Nature without suffering
Beach but not influencer hell
We are tired adults, be gentle
```

The first version of this should be rule-based and use saved tags and votes.

No AI is required.

### AI video parsing

AI video parsing is explicitly out of scope for normal development.

Treat this as a lottery-win feature only.

The app should be useful and enjoyable without AI.

## Non-goals

Do not build these for the MVP:

- AI video parsing
- Transcript parsing
- Automatic place extraction
- Flight search
- Hotel search
- Booking integrations
- Budget planning
- Multi-user account system
- Public sharing
- Full travel itinerary planning
- Complex recommendation engine
- 3D globe rendering

## First weekend target

By the end of the first weekend, the app should be able to do this:

```text
1. Add a YouTube video manually.
2. Create a journey for the video.
3. Add several stops manually with coordinates.
4. Display the stops as pins on a map.
5. Connect stops from the same journey with lines.
6. Click a pin to see the stop note and YouTube link.
```

A successful first demo could be:

```text
Video: Two Weeks in Japan by Train
Stops: Tokyo, Hakone, Kyoto, Nara, Osaka
Map: pins connected by a journey line
Interaction: click Kyoto -> see note -> open YouTube timestamp
```

That is enough to prove the idea.

## Guiding sentence

Someday Atlas is a private map of places discovered while travel-dreaming through YouTube, where pins are memories and lines are journeys.
