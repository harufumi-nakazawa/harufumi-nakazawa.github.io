#!/bin/bash

# Convert combined GeoJSON file to vector tiles
# The combined file contains all years' data in a single file with a 'total' object

COMBINED_GEOJSON="geojson/immigrants_total_combined.geojson"
TILES_DIR="tiles"

# Check if combined GeoJSON exists
if [ ! -f "$COMBINED_GEOJSON" ]; then
    echo "Error: Combined GeoJSON file not found: $COMBINED_GEOJSON"
    echo "Please run combine_geojson.py first to create the combined file."
    exit 1
fi

# Create tiles directory
mkdir -p "$TILES_DIR"

# Check if tiles already exist
if [ -d "$TILES_DIR" ] && [ "$(ls -A $TILES_DIR 2>/dev/null)" ]; then
    echo "Tiles directory already exists. Use --force to overwrite."
    read -p "Overwrite existing tiles? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "Converting combined GeoJSON to vector tiles..."
echo "This may take a while as it processes all years' data..."

# Convert to vector tiles
# -z14: max zoom level 14 (good balance between detail and file size)
# -Z0: min zoom level 0
# --detect-shared-borders: Detect and preserve shared polygon boundaries (helps with connectivity)
# --no-simplification-of-shared-nodes: Don't simplify nodes that are shared between polygons
# --output-to-directory: output as directory structure instead of MBTiles
# --force: overwrite existing tiles
# --layer: name the layer 'migration'
# --no-tile-compression: disable gzip compression for easier local debugging
tippecanoe \
    -z14 \
    -Z0 \
    --full-detail=18 \
    --low-detail=14 \
    --detect-shared-borders \
    --coalesce-densest-as-needed \
    --output-to-directory="$TILES_DIR" \
    --force \
    --layer=migration \
    --no-tile-compression \
    "$COMBINED_GEOJSON"

echo "Conversion complete! Tiles saved to $TILES_DIR"
