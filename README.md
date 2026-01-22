# Perspective Image Scoring Pipeline

A pipeline for sampling and scoring perspective images extracted from panoramic/HDRI images using AI vision models (Gemini and Qwen).

## Overview

This pipeline consists of three main components:

1. **Sampling** (`sample_perspectives.py`) - Randomly samples perspective images from a larger dataset
2. **Scoring with Gemini** (`gemini_scorer.py`) - Scores images using Google's Gemini API
3. **Scoring with Qwen** (`qwen_scorer.py`) - Scores images using Qwen via OpenRouter API

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

For Gemini, edit the `API_KEY` variable directly in `gemini_scorer.py`.

## Usage

### Step 1: Sample Images

#### Expected Input Folder Structure

The sampling script expects a specific folder organization:

```
input_directory/                          # e.g., ~/geocalib/data/openpano/rgb/train/
├── location_1/                           # Subfolder for each location/scene
│   ├── location_1_0_0.jpg               # <place_name>_<view_id>_<perspective_id>.jpg
│   ├── location_1_0_1.jpg               # Same location, same view (0), different perspective (1)
│   ├── location_1_0_2.jpg
│   ├── location_1_1_0.jpg               # Same location, different view (1)
│   ├── location_1_1_1.jpg
│   └── ...
├── location_2/
│   ├── location_2_0_0.jpg
│   └── ...
└── ...
```

**Naming Convention:** `<place_name>_<view_id>_<perspective_id>.jpg`

| Component        | Description                                   | Example                 |
| ---------------- | --------------------------------------------- | ----------------------- |
| `place_name`     | Location/scene name (can contain underscores) | `museum_of_history_16k` |
| `view_id`        | Camera viewpoint index within the location    | `5`                     |
| `perspective_id` | Specific perspective crop from that view      | `3`                     |

**Example filename:** `museum_of_history_16k_5_3.jpg`

- Location: `museum_of_history_16k`
- View ID: `5`
- Perspective ID: `3`

#### Sampling Logic

1. Randomly selects location subfolders
2. For each location, groups images by `view_id`
3. Picks one view that has at least N perspectives available
4. Randomly samples exactly N perspective images from that view
5. Copies sampled images to output folder, preserving location subfolders

#### Run Sampling

```bash
python sample_perspectives.py --num-views 10 --perspectives-per-view 4
```

This samples 40 images (10 views × 4 perspectives) into the `sampled_images/` folder and creates a `sampling_manifest.txt` log.

**Options:**

```bash
python sample_perspectives.py --input-dir /path/to/images --output-dir ./sampled_images
python sample_perspectives.py --seed 42  # for reproducibility
```

### Step 2: Score Images

**Using Gemini:**

```bash
python gemini_scorer.py
```

**Using Qwen:**

```bash
python qwen_scorer.py
```

## Output

The scorers generate Excel files with:

- Image ID and embedded image preview
- Scores for each evaluation component
- Justifications for each score
- Total score out of 10
- Best image per view highlighted in green

### Evaluation Components

| Component             | Max Score | Description                    |
| --------------------- | --------- | ------------------------------ |
| Subject Emphasis      | 2         | Clarity of subject focus       |
| Viewpoint Creativity  | 2         | Intentionality of camera angle |
| Compositional Balance | 2         | Visual weight distribution     |
| Spatial Harmonization | 4         | Depth and spatial coherence    |
| **Total**             | **10**    | Sum of all components          |

## File Structure

```
Final Pipeline/
├── sample_perspectives.py    # Image sampling script
├── gemini_scorer.py          # Gemini-based scorer
├── qwen_scorer.py            # Qwen-based scorer
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not in git)
├── .gitignore
├── README.md
├── sampled_images/           # Sampled images (not in git)
│   └── <location>_<view_id>/
│       └── <location>_<view_id>_<perspective_id>.jpg
├── sampling_manifest.txt     # Sampling log (generated)
├── perspective_scores_gemini.xlsx  # Gemini results (generated)
└── perspective_scores_qwen.xlsx    # Qwen results (generated)
```

## Configuration

Edit the configuration section at the top of each script:

- `IMAGE_FOLDER` - Path to sampled images
- `OUTPUT_FILE` - Output Excel filename
- `MODEL_NAME` - AI model to use
- `API_KEY` - API key (Gemini only)

## Notes

- Gemini scorer includes rate limiting (6 second delay between requests)
- Partial results are saved every 5 images
- Minimum score per component is enforced (total minimum: 5/10)
