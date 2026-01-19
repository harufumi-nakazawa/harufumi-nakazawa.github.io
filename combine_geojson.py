#!/usr/bin/env python3
"""
Combine multiple GeoJSON files (one per year) into a single GeoJSON file
where each feature has a 'total' object with year keys.
"""

import json
import os
from collections import defaultdict
from pathlib import Path

GEOJSON_DIR = "/Users/hnaka24/Dropbox (Personal)/japan_migration/output/GeoJSON"
OUTPUT_FILE = "geojson/immigrants_total_combined.geojson"

def combine_geojson_files():
    """Combine all year-specific GeoJSON files into one."""
    
    # Get all GeoJSON files
    geojson_files = sorted(Path(GEOJSON_DIR).glob("immigrants_total_*.geojson"))
    
    if not geojson_files:
        print(f"No GeoJSON files found in {GEOJSON_DIR}")
        return
    
    print(f"Found {len(geojson_files)} GeoJSON files")
    
    # Dictionary to store features by coordinates (primary key)
    # Using coordinates is more robust because municipal boundaries can change over time
    features_dict = {}
    
    # Track FIPS codes to detect duplicates (for debugging/warning)
    fips_to_coords = {}  # Map FIPS -> list of coordinate keys
    
    # Process each year file
    for geojson_file in geojson_files:
        year = int(geojson_file.stem.split('_')[-1])
        print(f"Processing {geojson_file.name} (year {year})...")
        
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for feature in data['features']:
            # Create a key from the geometry (use first coordinate pair)
            # This is robust because it matches by actual location, handling boundary changes
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0][0]
            elif feature['geometry']['type'] == 'MultiPolygon':
                coords = feature['geometry']['coordinates'][0][0][0]
            else:
                continue
            
            # Use first coordinate as key (longitude, latitude)
            # Round to 6 decimal places (~0.1 meter precision)
            key = (round(coords[0], 6), round(coords[1], 6))
            
            fips = feature['properties'].get('fips')
            total_value = feature['properties'].get('total')
            
            # Track FIPS codes for duplicate detection
            if fips:
                if fips not in fips_to_coords:
                    fips_to_coords[fips] = []
                if key not in fips_to_coords[fips]:
                    fips_to_coords[fips].append(key)
            
            # Initialize feature if not seen before
            if key not in features_dict:
                features_dict[key] = {
                    'type': 'Feature',
                    'geometry': feature['geometry'],
                    'properties': {
                        'fips': fips,
                        'prefecture': feature['properties'].get('prefecture'),
                        'city': feature['properties'].get('city'),
                        'district': feature['properties'].get('district')
                    }
                }
            
            # Add year value as a separate property (e.g., total_2006, total_2007, etc.)
            if total_value is not None:
                features_dict[key]['properties'][f'total_{year}'] = float(total_value)
    
    # Handle duplicate FIPS codes: merge data from all geometries with same FIPS
    # This handles cases where municipal boundaries changed but FIPS code stayed same
    print("\nChecking for duplicate FIPS codes (municipal boundary changes)...")
    duplicates_found = False
    for fips, coord_keys in fips_to_coords.items():
        if len(coord_keys) > 1:
            duplicates_found = True
            print(f"  FIPS {fips} appears in {len(coord_keys)} different geometries - merging data...")
            
            # Choose the first geometry as primary (usually the most recent or most complete)
            primary_key = coord_keys[0]
            primary_feature = features_dict[primary_key]
            
            # Merge all year data from other geometries into primary
            for other_key in coord_keys[1:]:
                if other_key in features_dict:
                    other_feature = features_dict[other_key]
                    # Copy any missing year data from other feature
                    for prop_key, prop_value in other_feature['properties'].items():
                        if prop_key.startswith('total_') and prop_key not in primary_feature['properties']:
                            primary_feature['properties'][prop_key] = prop_value
                    
                    # Remove the duplicate feature
                    del features_dict[other_key]
    
    if not duplicates_found:
        print("  No duplicate FIPS codes found.")
    
    # Convert to list
    combined_features = list(features_dict.values())
    
    # Create combined GeoJSON
    combined_geojson = {
        'type': 'FeatureCollection',
        'features': combined_features
    }
    
    # Create output directory
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Write combined file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined_geojson, f, ensure_ascii=False, indent=2)
    
    print(f"\nCombined {len(combined_features)} features")
    print(f"Output written to {OUTPUT_FILE}")
    
    # Print sample to verify structure
    if combined_features:
        sample = combined_features[0]
        print(f"\nSample feature:")
        print(f"  Properties: {json.dumps(sample['properties'], indent=2, ensure_ascii=False)}")

if __name__ == '__main__':
    combine_geojson_files()
