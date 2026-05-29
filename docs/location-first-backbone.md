# Location-First Backbone

This document describes the current places-first architecture in Someday Atlas.

The app began with a video-first route model, but the working product direction is now centered on saved places, especially root locations.

## Why this exists

The original model made videos the primary object:

`Video -> Journey -> Stops`

That was enough to prove the initial idea, but it duplicated place data and made the atlas awkward once the same place appeared in many videos or once a place contained multiple meaningful sub-locations.

Examples:

- `Tokyo` can contain `Shibuya`, `Tokyo Station`, `teamLab Planets`, and `Park Hyatt Tokyo`.
- `Cozumel` can appear in many different creator videos with different timestamps and notes.
- `Miami` can participate in many different route ideas without belonging to just one video-owned journey.

The places-first backbone makes the atlas reusable and accumulative instead of rebuilding the same place structure per video.

## Core direction

The main organizing object is now the saved location.

In practice:

- root locations are the anchor points of the atlas
- child locations add useful specificity under those anchors
- videos are linked to places as appearances
- place-owned journeys are rooted at locations and built from saved locations
- the map renders both locations and route lines

The older `video -> journey -> stop` model still exists for compatibility, but new product thinking should start from places.

## Main objects

### `Location`

Represents any atlas node, including:

- city
- district
- port
- attraction
- hotel
- mall
- station
- generic place

Locations are hierarchical through `parent_location_id`.

Root locations matter most because they anchor the place tree and the broader shape of the atlas.

### `VideoLocationAppearance`

Represents a saved video's appearance at a location.

Fields currently include:

- `video_id`
- `location_id`
- optional `timestamp_seconds`
- optional `order_index`
- optional `note`

This lets a place collect supporting source material without making the video the container for everything.

### `LocationJourney`

Represents a route concept rooted at a saved location.

Fields currently include:

- `root_location_id`
- `name`
- optional `description`

### `LocationJourneyStop`

Represents an ordered saved-location stop inside a place-owned journey.

Fields currently include:

- `journey_id`
- `location_id`
- `order_index`
- optional `note`

## What is implemented now

Implemented now:

1. Create root locations at `/locations`
2. Add child locations under any saved location
3. Edit locations on dedicated pages
4. Use geocoding helpers to find and fill location data
5. Attach saved videos to a location with optional timestamp and note
6. Aggregate appearances across a location subtree on the location detail page
7. Create place-owned journeys rooted at a location
8. Add saved locations as ordered stops on a place-owned journey
9. Render legacy video journeys and place-owned journeys together on the atlas map
10. Use a root-location-first home page instead of a video-led dashboard

## What still remains transitional

The older model has not been removed yet.

Still transitional:

1. Legacy video journeys still exist in the schema and UI
2. Some UI and route names still reflect older concepts
3. Place-owned journeys do not yet have a richer evidence model that combines video links and captures directly on the journey itself

## Current design consequences

Because root locations are key, UI and product decisions should generally follow these rules:

1. start navigation from locations when possible
2. make location pages the main place for structure and editing
3. treat videos as linked context rather than primary containers
4. keep child-location creation easy and low-friction
5. favor compact, readable browsing over dense dashboards

## Likely next direction

The most likely architectural next steps are:

1. enrich place-owned journeys with linked evidence from videos and captures
2. add better editing and reordering support for route stops
3. decide whether legacy video-owned journeys should be retired, migrated, or left as a compatibility layer
4. support per-place uploaded imagery while keeping a local fallback visual treatment

## Key query behavior

One of the most useful queries now supported is:

`location subtree -> all attached video appearances`

That means a `Tokyo` page can surface:

- direct Tokyo video appearances
- video appearances attached to districts and attractions under Tokyo
- child places that make the larger place browsable
- place-owned journeys rooted at or passing through the saved place

## Summary

The location-first backbone is no longer just an experiment.

It is the current product direction: root locations anchor the atlas, child places grow it, videos support it, and journeys connect the places that matter.