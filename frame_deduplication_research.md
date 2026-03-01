# Frame Deduplication and Keyframe Selection — Technical Research Report

**Date:** 1 March 2026  
**Prepared by:** Engineering  
**Purpose:** Evaluate alternatives to the current SSIM-based frame deduplication approach and recommend changes for the video-to-catalog pipeline.

---

## 1. Executive Summary

Our current frame extraction pipeline extracts every frame from the source video (approximately 300 frames for a 10-second clip at 30fps), applies a blur filter, and then uses SSIM (Structural Similarity Index) to remove duplicates. Despite tuning, this approach still produces 40–140 frames — far more than what the downstream image generation model can reasonably process.

This report evaluates five alternative approaches to frame deduplication and keyframe selection. Based on this analysis, the recommended path forward is a hybrid pipeline combining FFmpeg scene-change extraction, perceptual hashing, and optionally CLIP-based semantic clustering, which can reliably reduce the frame count to a controlled target (e.g., 10–15 frames) while maximizing content diversity.

---

## 2. Current State Analysis

### 2.1 Existing Pipeline

The current pipeline consists of the following stages:

1. **Full frame extraction** via FFmpeg — every frame is decoded and saved as JPEG
2. **Blur rejection** using Laplacian variance (threshold: 100)
3. **SSIM-based deduplication** — pairwise structural similarity on 256x256 grayscale thumbnails (threshold: 0.95)
4. **Top-N selection** by sharpness score

### 2.2 Identified Problems with SSIM

| Issue | Description |
|-------|-------------|
| **Pixel-level sensitivity** | SSIM compares luminance, contrast, and structural information at the pixel level. Minor camera panning, lighting changes, or slight object motion can drop the SSIM score below the threshold, causing semantically identical frames to be treated as unique. |
| **Fragile threshold** | At 0.95, the pipeline retains approximately 140 frames. Raising the threshold to 0.98 or higher causes useful frames to be incorrectly dropped. No single threshold value produces consistent results because the metric does not understand content. |
| **Quadratic time complexity** | Each candidate frame is compared against all previously accepted frames, resulting in O(n squared) comparisons. This becomes a bottleneck as frame count increases. |
| **Grayscale-only comparison** | Color information is discarded. Two frames with identical structural layout but different products (e.g., a red shirt vs. a blue shirt) may be incorrectly merged as duplicates. |
| **No semantic understanding** | SSIM has no concept of whether two frames depict the same product. It operates purely on pixel structure. |

---

## 3. Evaluated Approaches

### 3.1 FFmpeg Scene-Change Extraction

**Concept:** Instead of extracting all frames and filtering afterwards, use FFmpeg's built-in scene-change detection filter to extract only frames where significant visual change occurs.

**How it works:**
- FFmpeg computes a scene-change score (0.0 to 1.0) between consecutive frames during the decoding pass
- A threshold parameter (e.g., 0.3) determines the minimum change required to emit a frame
- A time-based fallback (e.g., at least one frame every 2 seconds) ensures coverage even during static segments

**Expected output:** 5–20 frames for a typical 10-second product video.

**Advantages:**
- Extremely fast — runs as part of the native FFmpeg decoding pipeline with no additional processing
- Eliminates the need to write and then re-read hundreds of intermediate JPEG files
- No additional Python dependencies required

**Limitations:**
- Does not understand product-level semantics; only detects visual change
- Threshold requires tuning per video style (slow pans vs. quick cuts)

---

### 3.2 Perceptual Hashing (pHash / dHash)

**Concept:** Replace SSIM with perceptual hashing. Each frame is converted to a compact fixed-size hash that is robust to minor visual changes. Frames are considered duplicates if their hash distance is below a threshold.

**How it works:**
- Each frame is resized, converted to frequency domain (via DCT for pHash), and reduced to a binary hash (typically 64 to 256 bits)
- Comparison is done via Hamming distance — a simple XOR-and-count operation
- Frames with Hamming distance below a threshold (e.g., 10 bits out of 256) are considered duplicates

**Performance comparison against SSIM:**

| Metric | SSIM | Perceptual Hash |
|--------|------|-----------------|
| Comparison cost per pair | O(W x H) — full pixel scan | O(1) — integer XOR |
| Robustness to camera motion | Low — sensitive to shifts | High — tolerates resize and recolor |
| Robustness to brightness change | Low | High |
| Semantic awareness | None | None |

**Threshold guidelines (for 256-bit pHash):**
- 6–8 bits: strict deduplication (removes only near-identical frames)
- 10–15 bits: moderate deduplication (recommended starting point)
- 20+ bits: aggressive deduplication (risk of merging distinct scenes)

**Advantages:**
- 100x to 1000x faster than SSIM for pairwise comparison
- More tolerant of lighting variation, camera motion, and minor color shifts
- Well-established library support (Python `imagehash` package)

**Limitations:**
- Still lacks semantic understanding — does not know whether two frames show the same product
- Requires a separate library dependency

---

### 3.3 PySceneDetect (Shot Boundary Detection)

**Concept:** Use a purpose-built scene detection library to segment the video into distinct shots, then extract one representative frame (keyframe) per shot.

**How it works:**
- PySceneDetect's `ContentDetector` analyzes consecutive frames in HSV color space to detect abrupt cuts
- Its `AdaptiveDetector` uses a rolling average threshold, making it more robust against false positives caused by camera motion
- The library returns a list of scene boundaries (start and end timecodes)
- A keyframe can be selected from the midpoint of each scene

**Advantages:**
- Designed specifically for shot boundary detection — handles both fast cuts and gradual transitions
- Configurable minimum scene length prevents over-segmentation
- Well-maintained open-source project

**Limitations:**
- Operates on the video file directly, not on pre-extracted frames
- Adds a runtime dependency
- Does not provide semantic understanding of frame content

---

### 3.4 CLIP Embedding with Clustering

**Concept:** Use OpenAI's CLIP model to generate semantic embeddings for each frame, then apply KMeans clustering to group semantically similar frames. Select one representative frame per cluster to guarantee a fixed number of diverse keyframes.

**How it works:**
- Each frame is passed through the CLIP image encoder (ViT-B/32), producing a 512-dimensional feature vector
- Embeddings are L2-normalized to enable cosine similarity comparison
- KMeans clustering groups the embeddings into N clusters (where N equals the desired output frame count)
- The frame closest to each cluster centroid is selected as the representative keyframe

**Why this is particularly suited to this pipeline:**
- The downstream consumer is an image generation model. CLIP embeddings capture the same high-level semantic and visual features that generation models operate on.
- By setting N (number of clusters) directly, the output frame count is guaranteed — no threshold tuning required.
- KMeans inherently maximizes inter-cluster distance, ensuring the selected frames are maximally diverse.

**Advantages:**
- Full semantic understanding — can distinguish between different products even when pixel structure is similar
- Guarantees exactly N output frames
- Maximizes content diversity across the selected set

**Limitations:**
- Requires the CLIP model (~400 MB) and a PyTorch dependency
- GPU is recommended for acceptable throughput (~50ms per frame on GPU; slower on CPU)
- Higher implementation complexity compared to the other approaches

---

### 3.5 Hybrid Pipeline (Recommended Production Approach)

**Concept:** Combine multiple techniques in a staged pipeline, using fast methods for early filtering and semantic methods for final selection.

**Pipeline stages:**

```
Stage 1: FFmpeg Scene-Change + Interval Extraction
  Input:   10-second video at 30fps (300 frames)
  Method:  Scene-change score > 0.3, with 2-second fallback interval
  Output:  ~10–20 candidate frames
            |
            v
Stage 2: Blur Rejection (existing Laplacian variance filter)
  Method:  Reject frames with variance below 100
  Output:  ~8–15 sharp candidates
            |
            v
Stage 3a: Perceptual Hash Deduplication
  Method:  Remove near-identical frames (pHash distance <= 10)
  Output:  ~6–12 unique candidates
            |
            v
Stage 3b: CLIP Clustering (Final Selection)
  Method:  KMeans on CLIP embeddings, select closest frame to each centroid
  Clusters: min(candidate count, max_frames)
  Output:  Exactly N diverse keyframes
```

**Advantages:**
- Each stage progressively reduces the frame set, so the expensive CLIP processing only runs on a small candidate pool
- Retains the blur filter already implemented in the current pipeline
- Guarantees a controlled output frame count with maximum content diversity
- Any individual stage can be bypassed if the team determines it is unnecessary

---

## 4. Method Comparison Matrix

| Criterion | SSIM (Current) | 1fps Uniform | FFmpeg Scene-Change | Perceptual Hash | PySceneDetect | CLIP + Clustering | Hybrid |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Frame Reduction** | Poor (40–140) | Fixed (~10) | Good (5–20) | Good | Good (5–20) | Exact budget | Exact budget |
| **Processing Speed** | Slow (O(n^2)) | Instant | Fast (native) | Fast | Fast | Moderate | Good |
| **Accuracy** | Pixel-only | Content-blind | Visual-only | Visual-only | Shot-aware | Semantic | Semantic |
| **Handles Camera Panning** | Fails | N/A | Ignores | Tolerant | Handles | Invariant | Invariant |
| **Handles Lighting Changes** | Fails | N/A | May false-trigger | Tolerant | May false-trigger | Invariant | Invariant |
| **Guarantees N Frames** | No | Roughly | No | No | No | Yes | Yes |
| **Semantic Understanding** | None | None | None | None | None | Full | Full |
| **New Dependencies** | None (current) | None | None | imagehash, Pillow | scenedetect | torch, clip, sklearn | All of the above |
| **Implementation Effort** | Done | Trivial | Easy | Easy | Easy | Moderate | Moderate |

---

## 5. Key Questions Addressed

### 5.1 Is extracting one frame per second through FFmpeg a viable solution?

Partially. Uniform 1fps extraction reduces 300 frames to approximately 10 for a 10-second video, which is in the correct range. However, it has a fundamental limitation: it is temporally uniform, not content-aware.

- If a product is displayed from the same angle for 5 seconds, the result is 5 nearly identical frames.
- If 3 different products appear within a single second, only 1 will be captured.

A content-aware approach (FFmpeg scene-change filter or PySceneDetect) would be strictly superior, as it adapts to the actual visual content of the video.

### 5.2 Can the current SSIM approach be improved?

Marginal improvements are possible:

1. **Multi-Scale SSIM (MS-SSIM)** provides greater robustness across spatial scales, but remains pixel-level.
2. **Increasing the comparison resolution** from 256x256 to 512x512 retains more detail, at the cost of 4x slower computation.
3. **Using LAB color space** instead of grayscale would prevent false merges between visually distinct products that share the same structure.
4. **Sliding window comparison** (comparing against only the last N accepted frames instead of all) would reduce the quadratic complexity.

However, none of these modifications address the fundamental limitation: SSIM has no semantic understanding. A frame showing a red shoe and a frame showing a blue shoe may have SSIM above 0.95 (identical structure, different color), while two frames of the same shoe from slightly different angles may have SSIM below 0.80.

**Assessment:** Improving SSIM is not recommended. The engineering effort would be better spent adopting a fundamentally better approach.

### 5.3 How should we test accuracy?

Three evaluation strategies are recommended:

1. **Manual ground truth:** Select 3–5 representative test videos. For each, manually label which frames contain unique content and which are duplicates. Compare each method's output against this ground truth.
2. **Precision and recall metrics:**
   - Precision — What percentage of kept frames are truly unique?
   - Recall — What percentage of unique content in the video is captured?
3. **Downstream evaluation:** Since the ultimate goal is product detection followed by image generation, the most meaningful test is whether the product detector successfully identifies all distinct products from the selected frames. This is the practical accuracy metric that matters most.

---

## 6. Recommendations

The following implementation order is recommended, prioritized by impact-to-effort ratio:

### Priority 1: FFmpeg Scene-Change Extraction
**Effort:** Low (modification to frame_extractor.py only)  
**Impact:** High — expected to reduce frame count from 300 to 10–20 at the extraction stage itself, with no additional Python processing required. This change alone is expected to resolve approximately 80% of the current problem.

### Priority 2: Replace SSIM with Perceptual Hashing
**Effort:** Low (swap comparison logic in frame_filter.py; add imagehash dependency)  
**Impact:** Medium — significantly faster and more robust deduplication for any remaining near-duplicate frames that pass the scene-change filter.

### Priority 3: Add CLIP-Based Clustering as Final Selection
**Effort:** Moderate (new processing stage; adds PyTorch and CLIP dependencies)  
**Impact:** High for quality — guarantees exactly N diverse output frames with semantic understanding. Particularly valuable when tight control over the output frame count is required.

---

## 7. Dependencies Summary

| Approach | New Dependencies | Installation |
|----------|-----------------|--------------|
| FFmpeg Scene-Change | None (FFmpeg already in use) | N/A |
| Perceptual Hash | imagehash, Pillow | pip install imagehash Pillow |
| PySceneDetect | scenedetect (with OpenCV backend) | pip install scenedetect[opencv] |
| CLIP + Clustering | torch, clip-model, scikit-learn | pip install torch clip-model scikit-learn |

---

## 8. Next Steps

1. **Team discussion** — Review this report and agree on which approach(es) to adopt.
2. **Prototype** — Implement Priority 1 (FFmpeg scene-change) and evaluate frame counts across a set of test videos.
3. **Benchmark** — If further reduction is needed, add Priority 2 (perceptual hashing) and compare results.
4. **Evaluate** — Measure downstream product detection accuracy with the reduced frame set to confirm that key content is preserved.
