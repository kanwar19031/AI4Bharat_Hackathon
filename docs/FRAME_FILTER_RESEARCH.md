# Frame Filter Research: Blur Discard & Unique Frame Identification

**Role:** AI/Data Science — KiranaStudio  
**Scope:** Blur detection, duplicate/near-duplicate frame removal, prototype tradeoffs  
**Audience:** Technical decision-making; prototype then production path  
**Last Updated:** February 2026

---

## 1. Executive Summary

| Area | Design/Lead Spec | Research Verdict | Prototype Recommendation |
|------|------------------|-------------------|---------------------------|
| **Blur detection** | Laplacian variance, threshold 100 | Valid baseline; threshold is content-dependent. FFT and Tenengrad are stronger in uncontrolled settings. | **Keep Laplacian** for POC; make threshold configurable. Add **relative ranking** (keep top-k by score) to avoid absolute threshold brittleness. |
| **Duplicate detection** | SSIM ≥ 0.95, pairwise over sharp frames | Correct choice for perceptual “same frame” at low N. Consecutive-only is faster but can miss non-adjacent duplicates. | **Keep SSIM**; use **resized grayscale** (e.g. 256×256) for speed. For prototype (≈10–30 frames), **all-pairs is acceptable**; document O(n²) for scale. |
| **Order of operations** | Design: blur → dedup. Lead (r1): extract → SSIM → Laplacian | Blur-first reduces work for dedup and matches design. | **Blur first, then dedup** (align with design). |

**Bottom line:** The current design (Laplacian + SSIM, blur-then-dedup) is appropriate for a **fast, accurate prototype**. No hidden magic required—focus on **configurable thresholds**, **resize-before-SSIM**, and **optional FFT or Tenengrad** as a later accuracy upgrade.

---

## 2. Current Spec vs Lead Summary

### 2.1 Design (`design.md`)

- **Blur:** Laplacian variance; reject if &lt; 100; keep “acceptable” 100–500, “sharp” &gt; 500.
- **Dedup:** SSIM on grayscale; duplicate if similarity &gt; 0.95.
- **Pipeline:** Stage 1 filter by blur → Stage 2 pairwise duplicate removal → return top 5 sharpest unique frames.
- **Refs:** PyImageSearch Laplacian blur, scikit-image SSIM.

### 2.2 Lead / r1 Summary (`r1.md`)

- **Flow:** MediaConvert 1 fps → **Stage 2: SSIM dedup** (consecutive similar, &gt; 0.95) → **Stage 3: Laplacian** (keep if variance &gt; 100) → 3–5 frames to Bedrock.
- **Difference:** Order is SSIM then Laplacian; “consecutive similar frames” implies temporal/adjacent comparison.

### 2.3 Backend Implementation (`frame_filter.py`)

- **Order:** Blur filter first (Laplacian), then SSIM dedup (on 256×256 grayscale), then sort by blur score and take top `max_frames`.
- **Extras:** On duplicate match, **replace** with the sharper of the two (good refinement).
- **Thresholds:** `blur_threshold=100`, `ssim_threshold=0.95` (configurable).

**Reconciliation:** Design and current code use **blur-first then dedup**; r1 uses **SSIM then Laplacian**. Blur-first is preferable: it cuts the set before O(n²) SSIM, and Laplacian is cheaper than SSIM. Recommendation: **keep blur-first**; mention in docs that "consecutive" in r1 can be read as "after temporal ordering we compare" and that we do full pairwise among sharp frames for correctness at small n.

### 2.4 Lead vs Design vs Research (Side-by-Side)

| Aspect | Lead (r1) | Design (design.md) | Research / Best practice |
|--------|-----------|--------------------|---------------------------|
| **Pipeline order** | Extract → SSIM dedup → Laplacian | Blur filter → Dedup → Top 5 | Blur first then dedup (fewer SSIM calls). |
| **Blur metric** | Laplacian, &gt; 100 | Laplacian, &lt; 100 reject | Laplacian OK; add relative/percentile; FFT/Tenengrad optional. |
| **Dedup metric** | SSIM &gt; 0.95 (consecutive) | SSIM &gt; 0.95 (pairwise) | SSIM on resized gray; all-pairs at small n. |
| **Scope** | 3–5 frames to Bedrock | Top 5 sharpest unique | Align: top 5 after blur + dedup; “replace with sharper” on duplicate. |

---

## 3. Blur Detection: In-Depth

### 3.1 Why Blur Matters Here

- Downstream: Bedrock (Claude/Titan) and product detection work better on sharp frames.
- Goal: Drop motion blur / defocus so we send only usable frames and reduce cost and noise.

### 3.2 Laplacian Variance (Current Choice)

**Mechanism:** Second derivative (Laplacian) on grayscale; variance of the response. Sharp = high edge response = high variance; blur = low variance.

**Pros:**

- Single scalar, one line in OpenCV: `cv2.Laplacian(gray, cv2.CV_64F).var()`.
- Fast, no extra deps.
- Well-understood; Pech-Pacheco et al. (ICPR 2000), PyImageSearch, OpenCV comparative study.

**Cons:**

- **Threshold is content- and capture-dependent.** “100” is a common default but not universal; retail shelves (text, edges) can sit in a different range than natural scenes.
- Sensitive to noise (noise can inflate variance).
- Single global threshold can misclassify in varying lighting or resolution.

**References:**

- PyImageSearch: [Blur Detection with OpenCV](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv) — threshold tuning, per-dataset.
- OpenCV: [Autofocus – Comparative Study of Focus Measures](https://opencv.org/autofocus-using-opencv-a-comparative-study-of-focus-measures-for-sharpness-assessment/) — Laplacian among best for “sharpest frame” selection.

**Practical improvement for prototype:** Keep Laplacian; **do not rely on a fixed 100 alone**. Either:

- **Relative:** Rank all frames by Laplacian variance and keep top-k (e.g. top 50% or top 10), then dedup, then take top 5; or  
- **Adaptive:** Use a percentile of the per-video variance (e.g. keep above 25th percentile) so threshold adapts to the clip.

This keeps speed and simplicity while making behavior robust across videos.

### 3.3 Alternatives Considered

| Method | Speed | Accuracy / Robustness | Use in prototype? |
|--------|--------|------------------------|-------------------|
| **FFT (high-frequency energy)** | Slower (FFT + magnitude) | More robust to lighting; “far more robust than Laplacian” (PyImageSearch). | Optional upgrade; not required for POC. |
| **Tenengrad (Sobel)** | Similar to Laplacian | Strong edge-based sharpness; OpenCV study: “perfect sharp frames.” | Good alternative if Laplacian misbehaves. |
| **Brenner gradient** | Slightly faster | Good for defocus; less robust than Tenengrad/Laplacian. | Possible; Laplacian sufficient first. |
| **Sobel + variance** | Slightly heavier | Combines edge + intensity; robust. | Alternative if we want one step up. |
| **Entropy / local variance** | Fast (variance) / slower (entropy) | OpenCV: “selected blurred frames” in their test. | Not recommended for blur discard. |

**FFT (reference):** [OpenCV FFT for Blur Detection](https://pyimagesearch.com/2020/06/15/opencv-fast-fourier-transform-fft-for-blur-detection-in-images-and-video-streams/). Idea: blur attenuates high frequencies; compare magnitude in a high-frequency band to a threshold. More robust, more tuning (size of band, threshold).

**Academic:** Pertuz et al., “Analysis of focus measure operators for shape-from-focus” — 36 operators; Laplacian variance is a standard baseline.

**Recommendation:**  
- **Prototype:** Laplacian + configurable threshold + **relative/percentile-based** keep rule.  
- **Later:** If we see false accepts/rejects on real kirana footage, add FFT or Tenengrad as second opinion or replacement.

### 3.4 Threshold and Domain

- **100:** Common default; “reject if below” is fine as a floor, but for shelves we may need 50–150 or higher depending on resolution and lighting.
- **Best practice:** Log Laplacian variance for a sample of kirana videos; set threshold (or percentile) from that distribution.
- **Code:** Already configurable in `frame_filter.py` (`blur_threshold`). Add a small script or notebook to histogram variance over a few runs and document suggested range (e.g. “typical sharp 200–2000, blur &lt; 80” for our data).

---

## 4. Unique Frame Identification and Deduplication

### 4.1 Goal

- Avoid sending near-identical frames to Bedrock (cost and redundant products).
- “Unique” here = perceptually same or near-same frame (e.g. camera paused), not just byte-identical.

### 4.2 SSIM (Current Choice)

**Mechanism:** Structural Similarity (luminance, contrast, structure). Output in [−1, 1]; 1 = identical. Design uses 0.95 as duplicate threshold.

**Pros:**

- Perceptually meaningful; matches “looks the same” better than MSE.
- Well-supported (scikit-image); easy to use on grayscale.
- No training; deterministic.

**Cons:**

- Pairwise comparison is O(n²) in number of frames. At n ≈ 10–30 (post blur), this is fine (e.g. 30×29/2 = 435 comparisons); at hundreds of frames we’d want a faster filter (e.g. hash).

**Implementation detail (already in code):** Compare on **resized** grayscale (e.g. 256×256) to speed up SSIM and reduce sensitivity to tiny shifts. This is the right tradeoff for prototype.

**Reference:** scikit-image [structural_similarity](https://scikit-image.org/docs/stable/api/skimage.metrics.html#structural-similarity).

**Recommendation:** **Keep SSIM at 0.95** for prototype; keep **resize-before-SSIM** (256×256 or similar). Document that for large n we’d add a hash-based candidate step (see below).

### 4.3 Consecutive vs All-Pairs

- **Consecutive (r1 wording):** Compare frame i with i−1 (or i±1). Cost O(n). Captures “camera held still” duplicates. Can **miss** duplicates that are not adjacent (e.g. same shelf at t=1 and t=5).
- **All-pairs (design / current code):** Compare every pair among sharp frames. Cost O(n²). Catches all duplicate pairs; at n ≤ 30, cost is acceptable.

**Research:** Temporal consistency is used in large-scale video dedup (e.g. re-ranking, LSH); for “select 3–5 keyframes from 10–30,” full pairwise is standard and correct.

**Recommendation:**  
- **Prototype:** **All-pairs** among blur-filtered frames (current behavior).  
- **Scale:** If we ever have hundreds of frames, first reduce set by **consecutive** or **perceptual hash** candidate filtering, then run SSIM on candidates only.

### 4.4 Alternatives Considered

| Method | Speed | Accuracy (exact / near-duplicate) | Use in prototype? |
|--------|--------|------------------------------------|-------------------|
| **SSIM** | O(n²) per pair, ~ms per pair at 256² | High for “same frame” / small changes | **Yes** (current). |
| **Perceptual hash (pHash, dHash, aHash)** | O(n) encode + O(n²) or O(n) with LSH | Good for exact/light transform; poor for crops/rotation (imagededup benchmarks). | Use later as **fast filter** before SSIM if n large. |
| **CNN embeddings** | Slow (model forward per frame) | Best for near-duplicates (rotation, crop); overkill for “same frame.” | No for POC. |
| **MSE / histogram** | Fast | Weaker than SSIM for perception; histogram can miss structure. | Not recommended. |

**imagededup benchmarks (UKBench, exact/transformed):**  
- Exact duplicates: **dHash** with threshold 0 is fastest and perfect.  
- Near-duplicates (resize/rotate/crop): hashing is weak; **CNN** (e.g. 0.9 similarity) is best but ~10× slower.  
- Our case is “same or almost same frame” (little geometric change), so **SSIM is the right compromise** and hashing is not required for prototype.

**References:**

- [imagededup – Benchmarks](https://idealo.github.io/imagededup/user_guide/benchmarks/)  
- [Fast Video Deduplication and Localization With Temporal Consistency Re-Ranking](https://ieeexplore.ieee.org/document/10577179/) (temporal re-ranking at scale)

### 4.5 Replace-on-duplicate (Sharper Wins)

Current code: when two frames are SSIM-duplicates, **keep the one with higher Laplacian score**. That maximizes sharpness in the retained set. No change needed.

---

## 5. Pipeline Order and Implementation Checklist

### 5.1 Recommended Order (Matches Design and Code)

1. **Extract** frames (e.g. 1 fps or fixed count).
2. **Blur filter:** Laplacian variance; keep above threshold (or top-k / percentile).
3. **Dedup:** Pairwise SSIM on resized grayscale; keep unique set, replace duplicate with sharper.
4. **Select:** Sort by blur score descending; take top 5 (or configurable).

### 5.2 Implementation Checklist (Prototype)

- [ ] **Blur:** Laplacian variance; **configurable** threshold (default 100).  
- [ ] **Robustness:** Add **relative** keep rule: e.g. keep frames with variance in top 50% or top 10, then apply threshold as floor.  
- [ ] **Dedup:** SSIM on **resized grayscale** (e.g. 256×256); threshold 0.95 configurable.  
- [ ] **Dedup:** All-pairs among blur-passed frames (no need for consecutive-only at current n).  
- [ ] **Replace:** On duplicate, keep frame with **higher blur score**.  
- [ ] **Logging:** Log blur scores and SSIM match counts for tuning and debugging.  
- [ ] **Calibration:** Optional script to run on 5–10 kirana videos and histogram Laplacian variance to document “typical range” for our domain.

### 5.3 Optional (Post-Prototype)

- **Blur:** A/B Laplacian vs Tenengrad or FFT on real data; switch if Laplacian misbehaves.  
- **Dedup at scale:** If n &gt; 100, add perceptual hash (e.g. dHash) as candidate filter, then SSIM on candidates.  
- **Temporal:** If we move to longer videos, consider consecutive-first pass then all-pairs on reduced set.

---

## 6. Resources Summary

### 6.1 Blur Detection

| Resource | URL | Use |
|----------|-----|-----|
| PyImageSearch – Laplacian blur | https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv | Baseline; threshold tuning. |
| PyImageSearch – FFT blur | https://pyimagesearch.com/2020/06/15/opencv-fast-fourier-transform-fft-for-blur-detection-in-images-and-video-streams/ | More robust alternative. |
| OpenCV – Focus measures comparison | https://opencv.org/autofocus-using-opencv-a-comparative-study-of-focus-measures-for-sharpness-assessment/ | Laplacian, Tenengrad, Brenner, Sobel+variance. |
| Pertuz et al. (focus measures survey) | Semantic Scholar / ResearchGate: “Analysis of focus measure operators for shape-from-focus” | 36 operators; theory. |
| Pech-Pacheco et al. (Laplacian in microscopy) | ICPR 2000, “Diatom autofocusing in brightfield microscopy” | Original Laplacian variance usage. |

### 6.2 Duplicate / Near-Duplicate Frames

| Resource | URL | Use |
|----------|-----|-----|
| scikit-image SSIM | https://scikit-image.org/docs/stable/api/skimage.metrics.html#structural-similarity | Implementation reference. |
| imagededup benchmarks | https://idealo.github.io/imagededup/user_guide/benchmarks/ | Hash vs CNN; exact vs near-duplicate. |
| IEEE – Video dedup + temporal re-ranking | https://ieeexplore.ieee.org/document/10577179 | Scale and temporal consistency. |
| ACM – LSH + similarity ranking for video | https://dl.acm.org/doi/10.1145/3007669.3007725 | Fast dedup at scale. |

### 6.3 Code / Libraries

| Library | Purpose |
|---------|--------|
| OpenCV (`cv2`) | Laplacian, Sobel, resize, grayscale. |
| scikit-image (`skimage.metrics.structural_similarity`) | SSIM. |
| imagehash / imagededup | Optional: perceptual hashing if we scale dedup. |
| NumPy | FFT if we add FFT-based blur (optional). |

---

## 7. Tradeoff Summary (Prototype vs Accuracy vs Speed)

| Choice | Option A (faster / simpler) | Option B (more accurate / robust) | Recommendation for POC |
|--------|-----------------------------|-------------------------------------|--------------------------|
| Blur metric | Laplacian only | Laplacian + FFT or Tenengrad fallback | **Laplacian**; add relative/percentile rule. |
| Blur threshold | Fixed 100 | Per-video percentile or calibrated range | **Configurable 100** + optional “keep top-k by score.” |
| Dedup metric | SSIM on full res | SSIM on 256² (current) | **SSIM on 256²** (already done). |
| Dedup scope | Consecutive only | All-pairs | **All-pairs** (n small). |
| Dedup at scale | — | Hash then SSIM | **Defer** until n &gt; ~100. |

**Conclusion:** The current design is already well-aligned with “fast and accurate” for the prototype. The main improvements are **configurability**, **relative blur selection**, and **documented thresholds and scaling path**, not a wholesale algorithm change. Optional hidden paths for later: FFT/Tenengrad for blur, perceptual hash as a fast prefilter for dedup at scale.

---

## 8. Suggested Design Doc / Requirements Updates

If you fold this research into `design.md` or requirements:

1. **Algorithm Details (Section 8.1):** Note that threshold 100 is a default; recommend calibration on kirana footage and/or a relative rule (e.g. keep frames in top 50% by Laplacian variance before applying a minimum threshold).
2. **Frame Filter (Section 4.3):** Explicitly state "pairwise SSIM over all blur-passed frames" (not only consecutive) and "on duplicate, retain the frame with higher blur score."
3. **References:** Add OpenCV comparative study, PyImageSearch FFT blur, imagededup benchmarks, and Pertuz et al. focus-measure survey to Section 12.
4. **Non-functional:** Document that frame filter is O(n) for blur and O(k²) for dedup where k = number of blur-passed frames; for prototype k is small (~10–30).
5. **Scale path:** One-line note: "At higher frame counts, consider perceptual hash (e.g. dHash) as a candidate filter before SSIM, and/or consecutive-frame prefilter."
