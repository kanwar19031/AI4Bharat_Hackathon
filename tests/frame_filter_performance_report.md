# Frame Filter Service Performance Test Report

Date: 2026-02-26  
Scope: `backend/app/pipeline/frame_filter.py` performance only  
Library focus: `skimage.metrics.structural_similarity` (SSIM) with OpenCV Laplacian blur scoring

## Video Info
- Video: `sample_video/chips.mp4`
- Source FPS: `29.970`
- Total extracted frames available to filter: `301`

## Extraction Result 
- Extraction completed successfully in all 5 runs with `total_frames=301` each time.
- This report does not evaluate extractor behavior beyond this shared input consistency.

## Test Results (Frame Filter)

| Test | Log File | BLUR_THRESHOLD | SSIM_THRESHOLD | Sharp Candidates | Blurry Rejected | Unique/Selected | Final Retention | Filter Duration (s) | Throughput (input frames/s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `frame_pipeline_log.txt` | 100.0 | 0.95 | 286 | 15 | 245 | 81.40% | 138.151 | 2.18 |
| 2 | `frame_pipeline_log1.txt` | 100.0 | 0.80 | 286 | 15 | 181 | 60.13% | 125.957 | 2.39 |
| 3 | `frame_pipeline_log2.txt` | 150.0 | 0.80 | 242 | 59 | 142 | 47.18% | 78.614 | 3.83 |
| 4 | `frame_pipeline_log3.txt` | 190.0 | 0.80 | 189 | 112 | 94 | 31.23% | 40.915 | 7.36 |
| 5 | `frame_pipeline_log4.txt` | 200.0 | 0.60 | 179 | 122 | 26 | 8.64% | 10.369 | 29.03 |

## Knowledge Derived (From Filter Results)

1. With blur fixed at `100`, lowering SSIM threshold from `0.95` to `0.80` reduced selected frames from `245` to `181` and improved runtime (`138.151s` -> `125.957s`).
2. Increasing blur threshold (`100` -> `190`, SSIM=`0.80`) reduced candidate volume strongly (`286` -> `189`), which also reduced runtime (`125.957s` -> `40.915s`).
3. The most aggressive setup (`blur=200`, `ssim=0.60`) delivered the fastest run (`10.369s`) but retained only `26/301` frames (`8.64%`), indicating very high compression.
4. Runtime scales with candidate count and dedup workload; fewer sharp candidates materially reduce SSIM comparison cost.

