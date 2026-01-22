#!/usr/bin/env python3
"""
Perspective Image Sampling Pipeline

This script samples perspective images from a panoramic image dataset.
It randomly selects locations, views, and perspective images while
preserving traceability to the original data.

Default: 10 views x 4 perspectives = 40 images exactly

Usage:
    python sample_perspectives.py
    python sample_perspectives.py --num-views 10 --perspectives-per-view 4
    python sample_perspectives.py --seed 42  # for reproducibility
"""

import os
import re
import random
import shutil
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


# =============================================================================
# Configuration
# =============================================================================
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │  CHANGE THESE when running on a different cluster/machine:                  │
# │                                                                             │
# │  1. DEFAULT_INPUT_DIR  - Path to folder containing location subfolders      │
# │                          Each subfolder should contain perspective images   │
# │                          with naming format: <place>_<viewid>_<perspid>.jpg │
# │                                                                             │
# │  2. DEFAULT_OUTPUT_DIR - Path where sampled images will be copied to        │
# │                          This folder will be created if it doesn't exist    │
# |                                                                             │
# |  3. SLURM SCRIPT       - Change env activation in run_sampling.sh to your   |
# |                            own env: source activate YOUR_ENV_NAME           │
# │                                                                             │
# │  Note: Use absolute paths. The ~ expands to user's home directory.          │
# │  Example: "/home/username/data/images/" or "~/data/images/"                 │
# └─────────────────────────────────────────────────────────────────────────────┘

# >>>>> CHANGE THIS: Path to your source image dataset <<<<<
DEFAULT_INPUT_DIR = os.path.expanduser("~/geocalib/data/openpano/rgb/train/")

# >>>>> CHANGE THIS: Path where sampled images will be saved <<<<<
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/geocalib/data/openpano/rgb/sampled/")

# Sampling parameters: 10 views x 4 perspectives = 40 images
# (Can also be changed via command line: --num-views and --perspectives-per-view)
DEFAULT_NUM_VIEWS = 10
DEFAULT_PERSPECTIVES_PER_VIEW = 4


# =============================================================================
# Filename Parsing
# =============================================================================

def parse_filename(filename: str) -> Optional[Tuple[str, int, int]]:
    """
    Parse a perspective image filename to extract components.

    Filename format: <place_name>_<view_id>_<perspective_id>.jpg

    Args:
        filename: The image filename (e.g., "museum_of_history_16k_5_3.jpg")

    Returns:
        Tuple of (place_name, view_id, perspective_id) or None if parsing fails
    """
    # Remove extension
    name = os.path.splitext(filename)[0]

    # Match pattern: everything up to last two underscore-separated numbers
    # Pattern: <anything>_<number>_<number>
    pattern = r'^(.+)_(\d+)_(\d+)$'
    match = re.match(pattern, name)

    if match:
        place_name = match.group(1)
        view_id = int(match.group(2))
        perspective_id = int(match.group(3))
        return (place_name, view_id, perspective_id)

    return None


def group_images_by_view(folder_path: str) -> Dict[int, List[str]]:
    """
    Group all images in a folder by their view_id.

    Args:
        folder_path: Path to the location subfolder

    Returns:
        Dictionary mapping view_id -> list of image filenames
    """
    view_groups = defaultdict(list)

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        parsed = parse_filename(filename)
        if parsed:
            _, view_id, _ = parsed
            view_groups[view_id].append(filename)

    return dict(view_groups)


# =============================================================================
# Sampling Logic
# =============================================================================

def sample_from_folder(
    folder_path: str,
    view_groups: Dict[int, List[str]],
    perspectives_per_view: int = 4
) -> List[str]:
    """
    Sample perspective images from a single folder (location).

    Randomly selects one view_id and samples exactly N perspective images from it.

    Args:
        folder_path: Path to the location subfolder
        view_groups: Dictionary mapping view_id -> list of image filenames
        perspectives_per_view: Exact number of perspectives to sample per view

    Returns:
        List of sampled image filenames (empty if insufficient images)
    """
    if not view_groups:
        return []

    # Filter views that have enough perspectives
    valid_views = {
        vid: files for vid, files in view_groups.items()
        if len(files) >= perspectives_per_view
    }

    if not valid_views:
        return []

    # Randomly select a view
    selected_view = random.choice(list(valid_views.keys()))
    available_images = valid_views[selected_view]

    # Sample exactly the required number of perspective images
    sampled_images = random.sample(available_images, perspectives_per_view)

    return sampled_images


def run_sampling_pipeline(
    input_dir: str,
    output_dir: str,
    num_views: int = 10,
    perspectives_per_view: int = 4,
    seed: Optional[int] = None
) -> Tuple[int, List[dict]]:
    """
    Execute the full sampling pipeline.

    Samples exactly (num_views x perspectives_per_view) images total.

    Args:
        input_dir: Path to the input dataset directory
        output_dir: Path to the output directory for sampled images
        num_views: Number of views to sample (each from a different location)
        perspectives_per_view: Number of perspective images per view
        seed: Random seed for reproducibility

    Returns:
        Tuple of (total_sampled_count, list of sample records)
    """
    if seed is not None:
        random.seed(seed)

    target_total = num_views * perspectives_per_view

    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get list of location subfolders
    subfolders = [
        d for d in os.listdir(input_path)
        if os.path.isdir(input_path / d)
    ]

    if not subfolders:
        raise ValueError(f"No subfolders found in: {input_dir}")

    print(f"Found {len(subfolders)} location subfolders")
    print(f"Target: {num_views} views x {perspectives_per_view} perspectives = {target_total} images\n")

    # Shuffle subfolders for random selection
    random.shuffle(subfolders)

    # Sampling loop
    views_sampled = 0
    total_images = 0
    sample_records = []

    folder_index = 0

    while views_sampled < num_views:
        # Check if we've exhausted all folders
        if folder_index >= len(subfolders):
            print(f"\nWARNING: Exhausted all {len(subfolders)} folders but only sampled {views_sampled} views.")
            print("Some folders may not have enough perspectives per view.")
            break

        folder_name = subfolders[folder_index]
        folder_path = input_path / folder_name
        folder_index += 1

        # Group images by view
        view_groups = group_images_by_view(str(folder_path))

        if not view_groups:
            print(f"  Skipping {folder_name}: no valid images found")
            continue

        # Sample from this folder
        sampled = sample_from_folder(
            str(folder_path),
            view_groups,
            perspectives_per_view
        )

        if not sampled:
            print(f"  Skipping {folder_name}: no view with {perspectives_per_view}+ perspectives")
            continue

        # Copy sampled images to output directory
        # Preserve structure: output_dir/<location>/<filename>
        location_output = output_path / folder_name
        location_output.mkdir(parents=True, exist_ok=True)

        parsed = None
        for img_filename in sampled:
            src = folder_path / img_filename
            dst = location_output / img_filename
            shutil.copy2(src, dst)

            # Parse for record keeping
            parsed = parse_filename(img_filename)
            if parsed:
                place_name, view_id, perspective_id = parsed
                sample_records.append({
                    'location': folder_name,
                    'filename': img_filename,
                    'view_id': view_id,
                    'perspective_id': perspective_id,
                    'source_path': str(src),
                    'dest_path': str(dst)
                })

        views_sampled += 1
        total_images += len(sampled)

        print(f"  [{views_sampled}/{num_views}] Sampled {len(sampled)} images from {folder_name} "
              f"(view_id={parsed[1] if parsed else 'unknown'})")

    return total_images, sample_records


def write_manifest(output_dir: str, sample_records: List[dict]) -> str:
    """
    Write a manifest file documenting all sampled images.

    This enables easy traceability back to original locations and views.

    Args:
        output_dir: Output directory path
        sample_records: List of sample record dictionaries

    Returns:
        Path to the manifest file
    """
    manifest_path = Path(output_dir) / "sampling_manifest.txt"

    with open(manifest_path, 'w') as f:
        f.write("# Perspective Image Sampling Manifest\n")
        f.write("# Format: location | view_id | perspective_id | filename\n")
        f.write("=" * 80 + "\n\n")

        # Group by location for readability
        by_location = defaultdict(list)
        for record in sample_records:
            by_location[record['location']].append(record)

        for location in sorted(by_location.keys()):
            f.write(f"\n## Location: {location}\n")
            f.write("-" * 40 + "\n")

            for record in sorted(by_location[location], key=lambda x: (x['view_id'], x['perspective_id'])):
                f.write(f"  view_id={record['view_id']:3d}  "
                       f"perspective_id={record['perspective_id']:3d}  "
                       f"-> {record['filename']}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Total images sampled: {len(sample_records)}\n")
        f.write(f"Total locations: {len(by_location)}\n")

    return str(manifest_path)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sample perspective images from panoramic dataset"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=DEFAULT_INPUT_DIR,
        help=f"Input dataset directory (default: {DEFAULT_INPUT_DIR})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for sampled images (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--num-views",
        type=int,
        default=DEFAULT_NUM_VIEWS,
        help=f"Number of views to sample (default: {DEFAULT_NUM_VIEWS})"
    )
    parser.add_argument(
        "--perspectives-per-view",
        type=int,
        default=DEFAULT_PERSPECTIVES_PER_VIEW,
        help=f"Perspectives per view (default: {DEFAULT_PERSPECTIVES_PER_VIEW})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)"
    )

    args = parser.parse_args()

    total_target = args.num_views * args.perspectives_per_view

    print("=" * 60)
    print("Perspective Image Sampling Pipeline")
    print("=" * 60)
    print(f"Input directory:  {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Views to sample: {args.num_views}")
    print(f"Perspectives per view: {args.perspectives_per_view}")
    print(f"Total images: {total_target}")
    print(f"Random seed: {args.seed}")
    print("=" * 60 + "\n")

    try:
        # Run the sampling pipeline
        total, records = run_sampling_pipeline(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            num_views=args.num_views,
            perspectives_per_view=args.perspectives_per_view,
            seed=args.seed
        )

        # Write manifest for traceability
        manifest_path = write_manifest(args.output_dir, records)

        print("\n" + "=" * 60)
        print("Sampling Complete!")
        print("=" * 60)
        print(f"Total images sampled: {total}")
        print(f"Output directory: {args.output_dir}")
        print(f"Manifest file: {manifest_path}")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
