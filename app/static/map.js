const BASEMAP_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}";
const BASEMAP_ATTRIBUTION = 'Tiles &copy; Esri; Sources: Esri, TomTom, Garmin, FAO, NOAA, USGS, OpenStreetMap contributors';

function createPopupHtml(journey, stop) {
    const placeBits = [stop.place_name, stop.country, stop.region].filter(Boolean).join(" · ");
    const note = stop.note ? `<p>${stop.note}</p>` : "";
    const timestamp = Number.isInteger(stop.timestamp_seconds)
        ? `<p><strong>Timestamp:</strong> ${stop.timestamp_seconds}s</p>`
        : "";
    const sourceKindLabel = journey.journey_type === "location" ? "Root location" : "Video";
    const sourceLine = journey.source_label
        ? `<p><strong>${sourceKindLabel}:</strong> ${journey.source_label}</p>`
        : "";
    const videoLink = stop.watch_url
        ? `<a href="${stop.watch_url}" target="_blank" rel="noreferrer">Open on YouTube</a>`
        : "";
    const locationLink = stop.location_detail_url
        ? `<a href="${stop.location_detail_url}">Open location</a>`
        : "";
    const journeyLink = journey.detail_url
        ? `<a href="${journey.detail_url}">Open route</a>`
        : "";
    const links = [videoLink, locationLink, journeyLink].filter(Boolean).join(" ");

    return `
        <div class="popup-card">
            <strong>${placeBits}</strong>
            <p><strong>Journey:</strong> ${journey.name}</p>
            ${sourceLine}
            ${timestamp}
            ${note}
            ${links}
        </div>
    `;
}

function createLocationPopupHtml(location) {
    const placeBits = [location.name, location.kind, location.country, location.region].filter(Boolean).join(" · ");
    const note = location.notes ? `<p>${location.notes}</p>` : "";
    const breadcrumb = (location.breadcrumb || []).length > 1
        ? `<p><strong>Path:</strong> ${location.breadcrumb.join(" / ")}</p>`
        : "";
    const directVideos = (location.videos || []).slice(0, 3).map((video) => {
        const timestamp = Number.isInteger(video.timestamp_seconds) ? ` (${video.timestamp_seconds}s)` : "";
        return `<li><a href="${video.watch_url}" target="_blank" rel="noreferrer">${video.title}${timestamp}</a></li>`;
    }).join("");
    const videoList = directVideos
        ? `<div><strong>Direct video links</strong><ul>${directVideos}</ul></div>`
        : "";

    return `
        <div class="popup-card">
            <strong>${placeBits}</strong>
            ${breadcrumb}
            <p><strong>Children:</strong> ${location.child_count}</p>
            <p><strong>Video links here:</strong> ${location.direct_appearance_count}</p>
            <p><strong>Video links in subtree:</strong> ${location.subtree_appearance_count}</p>
            ${note}
            ${videoList}
            <a href="${location.detail_url}">Open location</a>
        </div>
    `;
}

function renderJourneyMap() {
    const element = document.getElementById("journey-map");
    if (!element || typeof L === "undefined") {
        return;
    }

    const payload = JSON.parse(element.dataset.mapPayload || '{"journeys": []}');
    const journeys = payload.journeys || [];
    const locations = payload.locations || [];
    const map = L.map(element, {
        scrollWheelZoom: true,
    }).setView([20, 0], 2);

    L.tileLayer(BASEMAP_URL, {
        maxZoom: 19,
        attribution: BASEMAP_ATTRIBUTION,
    }).addTo(map);

    if (!journeys.length && !locations.length) {
        return;
    }

    const palette = ["#c85b34", "#2b7a78", "#7b5ea7", "#1d4e89", "#768948"];
    const allPoints = [];

    journeys.forEach((journey, index) => {
        const color = palette[index % palette.length];
        const linePoints = [];

        (journey.stops || []).forEach((stop) => {
            const point = [stop.latitude, stop.longitude];
            allPoints.push(point);
            linePoints.push(point);

            L.circleMarker(point, {
                radius: 8,
                weight: 2,
                color,
                fillColor: "#fffaf1",
                fillOpacity: 0.95,
            })
                .bindPopup(createPopupHtml(journey, stop))
                .addTo(map);
        });

        if (linePoints.length > 1) {
            L.polyline(linePoints, {
                color,
                weight: 3,
                opacity: 0.88,
            }).addTo(map);
        }
    });

    locations.forEach((location) => {
        const point = [location.latitude, location.longitude];
        allPoints.push(point);

        L.circleMarker(point, {
            radius: 9,
            weight: 2,
            color: "#0f766e",
            fillColor: "#d9fffb",
            fillOpacity: 0.92,
        })
            .bindPopup(createLocationPopupHtml(location))
            .addTo(map);
    });

    if (allPoints.length === 1) {
        map.setView(allPoints[0], 6);
    } else if (allPoints.length > 1) {
        map.fitBounds(allPoints, { padding: [40, 40] });
    }
}

function initializeCaptureProfiles() {
    const selectedProfileInput = document.getElementById("capture-created-by");
    const customInput = document.getElementById("capture-created-by-custom");
    const customField = document.getElementById("capture-custom-field");
    if (!selectedProfileInput || !customInput || !customField) {
        return;
    }

    const profileButtons = Array.from(document.querySelectorAll("[data-profile-value]"));
    if (!profileButtons.length) {
        return;
    }

    const syncActiveProfile = (value) => {
        profileButtons.forEach((button) => {
            button.classList.toggle("is-active", button.dataset.profileValue === value);
        });

        const hasSelectedProfile = Boolean(value);
        customField.classList.toggle("is-collapsed", hasSelectedProfile);
        customInput.disabled = hasSelectedProfile;
    };

    profileButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const nextValue = button.dataset.profileValue || "";
            const isAlreadySelected = selectedProfileInput.value === nextValue;

            selectedProfileInput.value = isAlreadySelected ? "" : nextValue;
            syncActiveProfile(selectedProfileInput.value);
            if (!isAlreadySelected) {
                customInput.value = "";
            } else {
                customInput.focus();
            }
        });
    });

    customInput.addEventListener("input", () => {
        if (customInput.value.trim()) {
            selectedProfileInput.value = "";
            syncActiveProfile("");
        }
    });

    syncActiveProfile(selectedProfileInput.value.trim());
}

function initializeCaptureCardLinks() {
    document.body.addEventListener("click", (event) => {
        const card = event.target.closest(".capture-card[data-capture-card-url]");
        if (!card || !window.matchMedia("(min-width: 900px)").matches) {
            return;
        }

        if (event.target.closest("a, button, input, select, textarea, label")) {
            return;
        }

        const destination = card.dataset.captureCardUrl;
        if (!destination) {
            return;
        }

        window.location.href = destination;
    });
}

function initializeGeocodeApplyButtons() {
    const fieldIdMap = {
        stop: {
            placeName: "stop-place-name",
            country: "stop-country",
            region: "stop-region",
            latitude: "stop-latitude",
            longitude: "stop-longitude",
        },
        location: {
            placeName: "location-name",
            country: "location-country",
            region: "location-region",
            latitude: "location-latitude",
            longitude: "location-longitude",
        },
    };

    document.body.addEventListener("click", (event) => {
        const button = event.target.closest(".geocode-apply-button");
        if (!button) {
            return;
        }

        const applyContext = button.dataset.applyContext || "stop";
        const selectedFieldIds = fieldIdMap[applyContext] || fieldIdMap.stop;
        const fieldMap = {
            placeName: document.getElementById(selectedFieldIds.placeName),
            country: document.getElementById(selectedFieldIds.country),
            region: document.getElementById(selectedFieldIds.region),
            latitude: document.getElementById(selectedFieldIds.latitude),
            longitude: document.getElementById(selectedFieldIds.longitude),
        };

        if (!fieldMap.placeName || !fieldMap.latitude || !fieldMap.longitude) {
            return;
        }

        fieldMap.placeName.value = button.dataset.placeName || "";
        fieldMap.country.value = button.dataset.country || "";
        fieldMap.region.value = button.dataset.region || "";
        fieldMap.latitude.value = button.dataset.latitude || "";
        fieldMap.longitude.value = button.dataset.longitude || "";

        const candidateList = button.closest(".geocode-candidate-list");
        if (candidateList) {
            candidateList.querySelectorAll(".geocode-candidate-card").forEach((card) => {
                card.classList.remove("is-selected");
            });
        }

        const selectedCard = button.closest(".geocode-candidate-card");
        if (selectedCard) {
            selectedCard.classList.add("is-selected");
        }

        fieldMap.placeName.focus();
    });
}

function renderGeocodePreviewMaps() {
    if (typeof L === "undefined") {
        return;
    }

    const previewMaps = document.querySelectorAll("[data-geocode-preview-map]");
    previewMaps.forEach((element) => {
        if (element.dataset.mapInitialized === "true") {
            return;
        }

        const latitude = Number.parseFloat(element.dataset.latitude || "");
        const longitude = Number.parseFloat(element.dataset.longitude || "");
        if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
            return;
        }

        const map = L.map(element, {
            attributionControl: false,
            zoomControl: false,
            dragging: false,
            doubleClickZoom: false,
            scrollWheelZoom: false,
            boxZoom: false,
            keyboard: false,
            tapHold: false,
            touchZoom: false,
        }).setView([latitude, longitude], 11);

        L.tileLayer(BASEMAP_URL, {
            maxZoom: 19,
            attribution: BASEMAP_ATTRIBUTION,
        }).addTo(map);

        L.marker([latitude, longitude]).addTo(map);
        element.dataset.mapInitialized = "true";
    });
}

function renderLocationPreviewMaps() {
    if (typeof L === "undefined") {
        return;
    }

    const previewMaps = document.querySelectorAll("[data-location-preview-map]");
    previewMaps.forEach((element) => {
        if (element.dataset.mapInitialized === "true") {
            return;
        }

        const latitude = Number.parseFloat(element.dataset.latitude || "");
        const longitude = Number.parseFloat(element.dataset.longitude || "");
        if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
            return;
        }

        const map = L.map(element, {
            attributionControl: false,
            scrollWheelZoom: false,
        }).setView([latitude, longitude], 10);

        L.tileLayer(BASEMAP_URL, {
            maxZoom: 19,
            attribution: BASEMAP_ATTRIBUTION,
        }).addTo(map);

        const marker = L.circleMarker([latitude, longitude], {
            radius: 9,
            weight: 2,
            color: "#0f766e",
            fillColor: "#d9fffb",
            fillOpacity: 0.92,
        }).addTo(map);

        if (element.dataset.label) {
            marker.bindPopup(`<strong>${element.dataset.label}</strong>`);
        }

        element.dataset.mapInitialized = "true";
    });
}

document.addEventListener("DOMContentLoaded", renderJourneyMap);
document.addEventListener("DOMContentLoaded", initializeCaptureProfiles);
document.addEventListener("DOMContentLoaded", initializeCaptureCardLinks);
document.addEventListener("DOMContentLoaded", initializeGeocodeApplyButtons);
document.addEventListener("DOMContentLoaded", renderGeocodePreviewMaps);
document.addEventListener("DOMContentLoaded", renderLocationPreviewMaps);
document.body.addEventListener("htmx:afterSwap", renderGeocodePreviewMaps);