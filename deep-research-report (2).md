# Building an Automated 3 m Satellite Change‑Detection App for Tehran and Isfahan

## Executive summary

A practical, automated “find the latest imagery → archive → detect changes → show on a web map + timelapse” application is easiest to build around **continuous delivery** from commercial providers, not around interactive viewers. In particular, Planet’s **Subscriptions API** is explicitly designed for continuous cloud delivery of imagery based on an AOI and time window and delivers new items automatically as they are published. citeturn14view3turn29view0turn13search1

For ~3 m imagery, **PlanetScope (PSScene)** is the primary commercial option with global coverage; its ortho products are exported at **3.0 m pixel size** (per the PSScene product specification). citeturn9search3turn9search11 PlanetScope also includes a publication lifecycle (`preview` → `standard` → `finalized`), and Planet documents that for PSScene items, **finalized** data is typically available **~12–24 hours after an item reaches standard**. citeturn16view0turn10search0

To make change detection reliable, you must treat **cloud masking and co‑registration** as first-class steps. Planet provides the **Usable Data Mask (UDM2/UDM2.1)** as an 8‑band GeoTIFF per image, classifying pixels (clear/cloud/haze/shadow/snow) and including a confidence band; UDMs are available globally for PlanetScope from August 2018 onward, and newer acquisitions are processed as UDM2.1. citeturn17view1turn34view0turn17view2turn35search2 Co‑registration matters because even orthorectified 3 m imagery can exhibit local misregistrations; published research on PlanetScope highlights orthorectification-related misregistrations and mitigation strategies (registration to reference imagery, removing global shifts, restricting view‑angle differences). citeturn21view0

Finally, note that the **Sentinel Hub EO Browser is being deprecated on March 20, 2026**, so treat it as a short‑term manual viewer and build your automation on APIs (Planet, aggregators, or Copernicus/Sentinel Hub endpoints). citeturn11search2turn11search13

## Data sources and access methods

### Provider comparison table

| Provider / platform | Typical spatial detail | Revisit & latency (practical) | Cost & licensing model | Primary access method(s) you can automate |
|---|---:|---|---|---|
| **entity["company","Planet Labs","earth imaging company"]** (PlanetScope / PSScene) | ~3 m ortho pixel size citeturn9search3turn9search11 | “Nearly all land daily” capture; publication lifecycle (preview/standard/finalized) citeturn16view0 | Contract/subscription; continuous delivery supported citeturn14view3turn29view0 | Data API quick-search for discovery + asset activation/download citeturn14view0turn14view1; Orders API (one-time) citeturn30view0turn14view2; Subscriptions API (continuous) citeturn14view3turn29view0turn34view1 |
| Planet (SkySat, optional) | sub‑meter (provider-specific) | tasking + archive; UDM available | commercial | Planet APIs (tasking/orders/subscriptions), depending on contract citeturn10search6turn17view1 |
| **entity["company","Maxar Technologies","commercial satellite company"]** (WorldView, optional) | 0.5 m pan / 2 m multispectral (through Sentinel Hub listing) citeturn19view0turn18view1 | archive + tasked acquisitions (not systematic) citeturn19view0 | commercial licensing | Maxar eAPI search/order to S3 citeturn24view0turn24view1turn24view2; or “WorldView via Sentinel Hub” ordering/import citeturn18view0turn18view1turn19view0 |
| **entity["company","Airbus Defence and Space","earth observation unit"]** (Pléiades Neo / SPOT, optional) | 30 cm to 1.5 m (product-dependent) citeturn25view0turn2search2 | archive + tasking | subscription (“Living Library”) or pay‑per‑order (PPO) citeturn25view0 | OneAtlas Search API + Order API endpoints citeturn25view2turn25view1 |
| **entity["company","BlackSky","geospatial intelligence company"]** (optional) | marketing states 35 cm imagery available citeturn2search3 | marketing claims “as little as 60 minutes” delivery and multiple revisits citeturn2search3 | commercial subscription | vendor portal/API (contract required) citeturn2search3 |
| **entity["company","UP42","geospatial marketplace"]** (aggregator) | varies by collection (Pléiades etc.) citeturn26view0turn26view1 | archive ordering flows | credits model (100 credits = €$1; min 10,000 credits) citeturn26view1 | STAC-like catalog search + order + delivery; EULA acceptance + access approvals for some collections citeturn26view0turn26view1 |
| **entity["company","SkyWatch","satellite imagery marketplace"]** (aggregator) | varies (including medium-res tiers) | marketplace-dependent | pay-as-you-use pricing listed by resolution tiers citeturn4search2 | marketplace ordering APIs/products (account required) citeturn4search2 |

### Choosing the “3 m primary + optional higher-res” strategy

For **3 m automated monitoring**, PlanetScope is the most straightforward because it offers (a) high cadence coverage, (b) automation-first APIs, and (c) per-image cloud usability masks (UDM2/UDM2.1). citeturn16view0turn14view3turn17view1

Optional sub‑meter sources (SkySat/Maxar/Airbus/BlackSky) are best integrated later, once your pipeline is stable, because they introduce additional constraints: ordering workflows, minimum areas, tasking windows, and stricter licensing. For example, Maxar eAPI’s “Quick Start” emphasizes orders delivered to AWS S3 and uses OAuth tokens that expire; Airbus OneAtlas exposes separate search and ordering endpoints with bearer-token auth. citeturn24view0turn24view2turn25view2turn25view1

## Architecture and AOI design

### Reference system architecture

```mermaid
flowchart TD
  A[Scheduler: cron / GitHub Actions / Cloud Scheduler] --> B[Collector]
  B --> C[Provider APIs: Planet + optional others]
  C --> D[Raw archive in object storage: S3/GCS (COG + metadata)]
  D --> E[Preprocess workers: cloud mask + coreg + resample]
  E --> F[Change detection workers: diff/indices/ML]
  F --> G[(PostGIS)]
  G --> H[Tile/API service]
  H --> I[Web map UI: time slider, before/after, timelapse]
  D --> I
```

Key components (minimal, production-friendly):
- **Collector service**: runs every 6 hours (or daily), searches each AOI, pulls new scenes, and writes into object storage.
- **Preprocess workers**: normalize imagery into a consistent projection/grid; apply cloud masks; generate COGs and browse PNGs.
- **Analytics workers**: compute change masks/events and store polygons + metadata in PostGIS.
- **API/tile service**: returns change events, serves vector tiles (MVT) and links to before/after rasters.
- **UI**: map + timeline slider + “before/after” compare + video timelapse.

This separation is aligned with how providers structure delivery (separate discovery, download, and processing) and helps you throttle each stage to respect provider rate limits. citeturn13search1turn23view1turn14view1

### AOIs for city-center monitoring

City centers (reference points):
- entity["city","Tehran","tehran province, iran"]: 35.6889, 51.3897 citeturn11search0  
- entity["city","Isfahan","isfahan province, iran"]: 32.66528, 51.67028 citeturn11search1  

Below are **~5 km × 5 km** CRS84 (lon,lat) AOIs around the city centers (small AOIs keep costs predictable and exports fast).

#### CRS84 BBOXes (paste-ready)

```json
{
  "tehran_bbox_crs84": [51.362049329675, 35.666442220625, 51.417350670325, 35.711357779375],
  "isfahan_bbox_crs84": [51.643602920397, 32.642822220625, 51.696957079603, 32.687737779375]
}
```

#### GeoJSON FeatureCollection (paste-ready)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "tehran_5km_box" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [51.362049329675, 35.666442220625],
          [51.417350670325, 35.666442220625],
          [51.417350670325, 35.711357779375],
          [51.362049329675, 35.711357779375],
          [51.362049329675, 35.666442220625]
        ]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "isfahan_5km_box" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [51.643602920397, 32.642822220625],
          [51.696957079603, 32.642822220625],
          [51.696957079603, 32.687737779375],
          [51.643602920397, 32.687737779375],
          [51.643602920397, 32.642822220625]
        ]]
      }
    }
  ]
}
```

Buffering guidance: if you later want “whole-city-ish” coverage, expand to 10–20 km boxes, but do it carefully—commercial pricing is often area-based, and larger AOIs increase cloud probability and processing/storage costs. citeturn14view3turn26view1

## Automated ingestion and preprocessing

### Recommended ingestion pattern for ~3 m: Planet Subscriptions delivering to cloud

Planet describes Subscriptions as its **recommended** API for customers needing **continuous data feed** over an AOI and states that it “automatically processes and delivers all items which meet your subscription criteria, as soon as they are published to the catalog.” citeturn14view3turn14view3turn13search4

Key subscription controls you will use:
- `start_time`, `end_time`, `time_range_type` (`acquired` vs `published`) citeturn34view1
- `publishing_stages` (`standard`, `finalized`) citeturn34view1turn16view0
- `asset_types` must be valid for the item type (Planet will validate) citeturn34view1turn32search4
- Optional server-side tools:
  - `clip` then `cloud_filter` for AOI-level cloud thresholds; Planet explicitly recommends using cloud_filter **after** clip, and notes it relies on UDM2-backed metadata (clear/cloud percent, etc.). citeturn36search4turn17view1

#### Step A: Determine the exact PSScene asset types available to your account (one-time)

Planet Data API exposes endpoints to list asset types and list assets for a specific item. citeturn32search4turn14view1

```bash
# List asset types available to your user
curl -s -u "$PL_API_KEY:" "https://api.planet.com/data/v1/asset-types" | head

# After you have an item id, list its assets:
curl -s -u "$PL_API_KEY:" \
  "https://api.planet.com/data/v1/item-types/PSScene/items/${ITEM_ID}/assets" | head
```

The “list assets” response includes activation links and (when active) a `location` URL for download. citeturn14view1turn13search0

Practical default for analytics: PlanetScope documentation highlights **surface reflectance** ortho assets (`*_sr`) for temporal monitoring and notes they take longer to generate and are typically available **8–12 hours after an item is published**. citeturn16view0

#### Step B: Create two subscriptions (one per AOI) with AOI clip + AOI-level cloud filtering

Planet’s Subscriptions “sources” schema shows the `source.parameters` block (item_types, asset_types, time range, geometry, publishing stages) and documents that if `publishing_stages` is omitted you typically get standard or finalized; adding it lets you control latency/quality tradeoffs. citeturn34view1turn16view0

**Paste-ready: “Tehran PSScene rolling feed” subscription request**  
(Replace the destination/delivery block with your chosen cloud destination; Planet supports cloud delivery in the subscription contract. citeturn14view3turn28search12)

```json
{
  "name": "tehran_psscene_3m_sr_feed",
  "source": {
    "type": "catalog",
    "parameters": {
      "item_types": ["PSScene"],
      "asset_types": ["<FILL_WITH_VALID_ASSET_TYPES>"],
      "start_time": "2026-03-06T00:00:00Z",
      "end_time": "2026-04-06T00:00:00Z",
      "time_range_type": "published",
      "publishing_stages": ["standard", "finalized"],
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [51.362049329675, 35.666442220625],
          [51.417350670325, 35.666442220625],
          [51.417350670325, 35.711357779375],
          [51.362049329675, 35.711357779375],
          [51.362049329675, 35.666442220625]
        ]]
      },
      "geometry_relation": "intersects"
    }
  },
  "tools": [
    { "clip": { "aoi": { "type": "Polygon", "coordinates": [[
      [51.362049329675, 35.666442220625],
      [51.417350670325, 35.666442220625],
      [51.417350670325, 35.711357779375],
      [51.362049329675, 35.711357779375],
      [51.362049329675, 35.666442220625]
    ]] } } },
    { "cloud_filter": { "cloud_percent": 40 } }
  ],
  "delivery": {
    "type": "<YOUR_DELIVERY_TYPE>",
    "parameters": { "<YOUR_DESTINATION_PARAMS>": "<FILL_ME>" }
  }
}
```

Why this is valid:
- Subscriptions use `start_time`/`end_time` rather than Data API DateRangeFilter. citeturn34view1  
- `publishing_stages` accepts `preview|standard|finalized` and delivers the latest stage if multiple match. citeturn34view1turn16view0  
- `cloud_filter` supports AOI-level thresholds after clipping and relies on UDM2-backed metadata. citeturn36search4turn17view1  

**Create it (cURL)**  
Planet’s Subscriptions “mechanics” page shows the create endpoint structure (you provide the subscription ID in the URL). citeturn29view0turn14view3

```bash
export SUBSCRIPTION_ID_TEHRAN="00000000-0000-0000-0000-000000000000" # use a real UUID
curl -sS -X POST "https://api.planet.com/subscriptions/v1/${SUBSCRIPTION_ID_TEHRAN}" \
  -H "Content-Type: application/json" \
  -u "$PL_API_KEY:" \
  -d @tehran_subscription.json
```

Repeat the same pattern for Isfahan by changing the geometry and subscription name.

### Alternative ingestion pattern: Data API quick-search + asset activation + download (6-hour polling)

The Data API “Item Search” page shows Quick Search with the endpoint and supports sorting by `acquired` or `published`. citeturn14view0turn36search0

**Quick search (last 6 hours) template**

```bash
FROM="2026-03-05T18:00:00Z"
TO="2026-03-06T00:00:00Z"

cat > tehran_quicksearch.json <<'JSON'
{
  "item_types": ["PSScene"],
  "filter": {
    "type": "AndFilter",
    "config": [
      {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": {
          "type": "Polygon",
          "coordinates": [[
            [51.362049329675, 35.666442220625],
            [51.417350670325, 35.666442220625],
            [51.417350670325, 35.711357779375],
            [51.362049329675, 35.711357779375],
            [51.362049329675, 35.666442220625]
          ]]
        }
      },
      {
        "type": "DateRangeFilter",
        "field_name": "published",
        "config": { "gte": "__FROM__", "lte": "__TO__" }
      }
    ]
  }
}
JSON

python3 - <<'PY'
import json
p="tehran_quicksearch.json"
d=json.load(open(p))
d["filter"]["config"][1]["config"]["gte"]="2026-03-05T18:00:00Z"
d["filter"]["config"][1]["config"]["lte"]="2026-03-06T00:00:00Z"
open(p,"w").write(json.dumps(d))
PY

curl -sS -X POST \
  "https://api.planet.com/data/v1/quick-search?_sort=published%20desc&_page_size=50" \
  -H "Content-Type: application/json" \
  -u "$PL_API_KEY:" \
  -d @tehran_quicksearch.json > results.json
```

Quick-search endpoint, sorting semantics, and request shape are shown in Planet’s Item Search docs. citeturn14view0turn36search0

**Asset activation + download loop (per item)**  
Planet documents that assets take minutes to activate; once active, they contain a `location` URL for download, and downloading consumes quota. citeturn14view1turn13search0

### Preprocessing checklist (what to do after files land in your bucket)

1. **Cloud masking**
   - For PlanetScope: use UDM2/UDM2.1 (clear/cloud/haze/shadow/snow) and optionally threshold by the confidence band. citeturn17view1turn34view0turn35search2  
   - For Sentinel-2 fallback: Sentinel Hub exposes s2cloudless probability/mask as CLP/CLM at 160 m. citeturn35search3turn35search7  

2. **Co‑registration**
   - Even when using orthorectified products, align each new scene to a stable reference (e.g., first clear scene in your archive), because multi-temporal misregistration can create false change. PlanetScope-specific misregistration issues and mitigation strategies are described in peer-reviewed literature. citeturn21view0  

3. **Resampling to a consistent grid**
   - Use `gdalwarp` to reproject/clip/resample. citeturn6search0  

4. **Store analysis-ready GeoTIFFs as COGs**
   - Use GDAL’s COG driver to write Cloud Optimized GeoTIFFs; GDAL documents the `COG` driver behavior and options. citeturn6search2turn6search5  

## Analytics, timelapse, and visualization

### Change detection methods that work well at ~3 m

**Baseline (fast, robust): masked pixel differencing + object extraction**
- Compute per-band absolute difference (e.g., RGB+NIR surface reflectance) between aligned “before” and “after”.
- Use robust thresholds (median/MAD on stable pixels) to avoid lighting/season artifacts.
- Convert the binary change raster into polygons and store event geometry, area, and timestamps.

GDAL provides a numpy-style raster calculator (`gdal_calc`) for band math/differencing. citeturn6search1  
For vectorization, `gdal_polygonize` generates polygons of connected pixel regions sharing a value and supports an eligibility mask. citeturn31search0

**Index differencing (when bands exist)**
- NDVI = (NIR − Red) / (NIR + Red) (useful to reduce false positives in vegetation areas), defined and widely used. citeturn5search7  
- NBR = (NIR − SWIR) / (NIR + SWIR) requires SWIR; it’s delivered for Landsat and Sentinel-2 style sensors, not typical 4‑band PlanetScope, so treat NBR as a **Sentinel‑2/Landsat complement**, not a PlanetScope-only method. citeturn6search3turn16view0  

### ML options (only after the baseline works)

- **U‑Net family**: widely used segmentation architecture; good for pixelwise change masks when trained on your labels. citeturn35search0  
- **Siamese / transformer change detection (e.g., ChangeFormer-style)**: designed for bitemporal inputs and competitive on change-detection benchmarks. citeturn35search1  

A pragmatic approach: start with baseline differencing to produce noisy “pseudo-labels,” then hand-correct a small dataset to train a U‑Net/Siamese model.

### Paste-ready: Python pseudocode for per‑AOI change detection + PostGIS storage

```python
# PSEUDOCODE (structure + key steps)

def process_new_scene(aoi_id, scene_id_after):
    before = db.get_latest_clear_scene(aoi_id, before=scene_id_after.acquired_at)
    after  = storage.load_cog(scene_id_after.cog_url)
    before_img = storage.load_cog(before.cog_url)

    # 1) Apply cloud mask (Planet: UDM2.1; Sentinel-2 fallback: CLP/CLM)
    after_mask  = storage.load_udm_mask(scene_id_after.udm_url)   # True=clear
    before_mask = storage.load_udm_mask(before.udm_url)

    # 2) Co-register (align after to before)
    aligned_after = coregister(after, before_img, mask=after_mask & before_mask)

    # 3) Compute robust change score
    diff = abs(aligned_after - before_img)  # per band
    score = diff.mean(axis="bands")

    # 4) Threshold + clean
    change_mask = score > robust_threshold(score, valid=after_mask & before_mask)
    change_mask = morphological_open_close(change_mask)

    # 5) Vectorize change regions + compute stats
    polygons = polygonize(change_mask)  # gdal_polygonize or rasterio.features.shapes
    for poly in polygons:
        area_m2 = db.sql("SELECT ST_Area($1::geography)", poly.wkt)
        bbox = poly.bounds
        confidence = compute_confidence(score, poly)

        # 6) Insert event
        db.insert_change_event(
            aoi_id=aoi_id,
            before_scene_id=before.id,
            after_scene_id=scene_id_after.id,
            bbox=bbox,
            geom=poly,
            area_m2=area_m2,
            confidence=confidence,
        )
```

PostGIS area-on-geography returns square meters (useful for consistent area metrics). citeturn7search2

### PostGIS schema and queries (paste-ready)

**Schema (minimal)**

```sql
CREATE TABLE aoi (
  aoi_id uuid PRIMARY KEY,
  name text NOT NULL,
  geom geometry(Polygon, 4326) NOT NULL
);

CREATE TABLE scene (
  scene_id text PRIMARY KEY,
  provider text NOT NULL,
  aoi_id uuid NOT NULL REFERENCES aoi(aoi_id),
  acquired_at timestamptz,
  published_at timestamptz,
  gsd_m numeric,
  cloud_meta jsonb,
  cog_url text NOT NULL,
  udm_url text,
  inserted_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE change_event (
  event_id bigserial PRIMARY KEY,
  aoi_id uuid NOT NULL REFERENCES aoi(aoi_id),
  before_scene_id text NOT NULL REFERENCES scene(scene_id),
  after_scene_id text NOT NULL REFERENCES scene(scene_id),
  detected_at timestamptz NOT NULL DEFAULT now(),
  confidence numeric,
  area_m2 double precision,
  geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX change_event_geom_gix ON change_event USING gist(geom);
CREATE INDEX change_event_time_idx ON change_event(detected_at);
```

**Query: events in AOI polygon over last 24 hours**

```sql
SELECT event_id, detected_at, confidence, area_m2
FROM change_event
WHERE aoi_id = $1
  AND detected_at >= now() - interval '24 hours'
ORDER BY detected_at DESC;
```

**Query: events intersecting a user-drawn polygon**

```sql
SELECT event_id, detected_at, confidence, area_m2
FROM change_event
WHERE ST_Intersects(
  geom,
  ST_SetSRID(ST_GeomFromGeoJSON($1), 4326)
);
```

`ST_Intersects` returns true when geometries share any point in common. citeturn8search2

### Visualization stack (web map + time slider + efficient delivery)

**Raster delivery**
- Store rasters as **COGs** so the UI (or a tile server) can request byte ranges efficiently; the COG format is intended for HTTP range requests and cloud hosting. citeturn6search2turn6search9

**Vector overlays**
- Serve change polygons as Mapbox Vector Tiles directly from PostGIS using `ST_AsMVT` + `ST_AsMVTGeom`, and generate tile bounds with `ST_TileEnvelope`. citeturn8search1turn8search7turn31search3

**Time slider UI**
- Mapbox GL JS provides a time slider example that filters features by time using the map’s filter mechanism. citeturn20search19turn20search3

### Timelapse generation (paste-ready)

1. For each timestamp, render a normalized RGB PNG (cloud-masked) on the same grid.
2. Use FFmpeg to compile an MP4.

```bash
# frames: frames/frame_0001.png, frames/frame_0002.png, ...
ffmpeg -framerate 2 -i frames/frame_%04d.png \
  -c:v libx264 -pix_fmt yuv420p timelapse.mp4
```

FFmpeg’s slideshow documentation describes using `-framerate` before the input for image sequences. citeturn9search10

## Operations, cost drivers, and safeguards

### Automation patterns that stay within quotas

**Planet rate limiting**
- Planet documents rate limiting behavior, recommends respecting `Retry-After` when present, and using exponential backoff; limits vary by API and plan. citeturn13search1turn13search2

**Copernicus / Sentinel Hub rate limiting and quotas (if you use Sentinel-2 fallback)**
- Copernicus Data Space Ecosystem documents monthly and per-minute quotas, a 4 concurrent connection limit, and rate-limiting behavior with `Retry-After` headers. citeturn23view0turn23view1  
- CDSE auth docs explicitly say: reuse access tokens; do not fetch a new token per request (token requests are rate-limited). citeturn22view0

### Rolling 24‑hour archive retention

If you want an always-on “last 24 hours” archive, implement **both**:
- storage-side lifecycle expiration, and
- app-side deletion of anything older than 24–72 hours (to handle delays and reprocessing).

Examples:
- **Amazon S3** supports lifecycle expiration actions to delete objects after a configured lifetime. citeturn20search0turn20search4  
- **Google Cloud Storage** supports Object Lifecycle Management rules for deleting/transitioning objects based on age/conditions. citeturn20search1turn20search9  

### GitHub Actions “every 6 hours” (paste-ready)

GitHub documents scheduled workflows with POSIX cron syntax. citeturn20search2

```yaml
name: ingest-and-detect

on:
  schedule:
    - cron: "0 */6 * * *"  # every 6 hours, UTC
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run pipeline
        env:
          PL_API_KEY: ${{ secrets.PL_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          STORAGE_BUCKET: ${{ secrets.STORAGE_BUCKET }}
        run: python -m app.pipeline.run --cities tehran isfahan --window-hours 24
```

### Cost drivers and ballpark thinking

Key cost drivers are (a) AOI area (km²), (b) image frequency per AOI, and (c) product type/band count (visual vs analytic vs surface reflectance), plus storage/egress. PlanetScope scene sizes are large (hundreds of km²), but your billing is typically driven by what you order/receive and your contract terms; Planet explicitly positions **Subscriptions** for bulk/ongoing delivery and **Orders** for smaller one-time orders. citeturn14view2turn14view3turn16view0

If you need a public “ballpark,” marketplaces sometimes publish per-km² starting points. For example, one SkyWatch pricing page lists “medium resolution” imagery starting at $2.50/km² and higher tiers at higher rates (illustrative only; actual availability and licensing vary). citeturn4search2  
UP42 quantifies spending in credits (100 credits = €$1, minimum 10,000 credits). citeturn26view1

### Security, ethics, and licensing safeguards

Because automated change detection can be misused, build safeguards into your system design:
- **Access control**: require user accounts; log access; separate admin-only raw imagery from public outputs.
- **Delay & aggregation**: consider delaying public event publication (e.g., 24–72 hours) and rounding coordinates (e.g., 100–250 m grids) for public views.
- **Policy compliance**: enforce provider EULAs (Planet/Maxar/Airbus/aggregators often require explicit EULA acceptance and restrict redistribution). UP42 explicitly requires EULA acceptance before first orders for some collections. citeturn26view0turn14view3turn19view0
- **Abuse resistance**: throttle API endpoints; implement backoff; monitor unusual query patterns; rotate credentials.

## Appendices

### Primary documentation links (copy/paste)

```text
Planet Data API Item Search (quick-search):
  https://docs.planet.com/develop/apis/data/item-search/

Planet Data API Items & Assets (activation + download):
  https://docs.planet.com/develop/apis/data/items/

Planet Rate Limiting:
  https://docs.planet.com/develop/rate-limiting/

Planet Subscriptions Overview + Sources + Mechanics:
  https://docs.planet.com/develop/apis/subscriptions/
  https://docs.planet.com/develop/apis/subscriptions/sources/
  https://docs.planet.com/develop/apis/subscriptions/mechanics/

PlanetScope publishing lifecycle + SR latency notes:
  https://docs.planet.com/data/imagery/planetscope/

Planet UDM (UDM2/UDM2.1):
  https://docs.planet.com/data/imagery/udm/

Maxar eAPI (search + order to S3):
  https://docs.eapi.maxar.com/home/quick_start/
  https://docs.eapi.maxar.com/home/user-guides/searching/
  https://docs.eapi.maxar.com/home/user-guides/ordering/

Airbus OneAtlas APIs overview + Search endpoint examples:
  https://api.oneatlas.airbus.com/getting-started/apis-overview/
  https://www.geoapi-airbusds.com/guides/oneatlas-data/g-search/

Copernicus Data Space Ecosystem (Sentinel Hub) Auth + Catalog + Process:
  https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Overview/Authentication.html
  https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Catalog.html
  https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Process.html

GDAL tools (gdalwarp, gdal_calc, COG, polygonize):
  https://gdal.org/en/stable/programs/gdalwarp.html
  https://gdal.org/en/stable/programs/gdal_calc.html
  https://gdal.org/en/stable/drivers/raster/cog.html
  https://gdal.org/en/stable/programs/gdal_polygonize.html

PostGIS functions (area, intersects, MVT):
  https://postgis.net/docs/ST_Area.html
  https://postgis.net/docs/ST_Intersects.html
  https://postgis.net/docs/ST_AsMVT.html
  https://postgis.net/docs/ST_AsMVTGeom.html
```

### Sentinel Hub / Copernicus fallback snippets (optional but useful)

If you want a secondary “free context layer” (Sentinel‑2) or want to unify processing via Sentinel Hub APIs, CDSE provides OAuth2-based auth and a STAC-like Catalog endpoint. citeturn22view0turn22view2turn22view1

**Token (CDSE)**
```bash
curl --request POST \
  --url "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token" \
  --header "content-type: application/x-www-form-urlencoded" \
  --data "grant_type=client_credentials&client_id=${CDSE_CLIENT_ID}" \
  --data-urlencode "client_secret=${CDSE_CLIENT_SECRET}"
```
Token reuse guidance is explicitly documented (don’t fetch a token per request). citeturn22view0