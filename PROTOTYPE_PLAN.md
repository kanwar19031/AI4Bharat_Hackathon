# KiranaStudio -- 7-Day Prototype Implementation Plan

**Objective:** Build a working prototype using the tech stack from `design.md` that demonstrates the full video-to-catalog pipeline.  
**Timeline:** 7 days (Feb 26 -- Mar 4, 2026)  
**Type:** Proof of Concept (POC), not MVP

---

## 1. Tech Stack for POC

### Compute & API: FastAPI (Python 3.11)

The design document specifies Python 3.11 and Boto3 as the backend language and AWS SDK. For the POC, instead of deploying individual Lambda functions behind API Gateway, we consolidate all backend logic into a **single FastAPI server**. This gives us:

- Hot reload during development
- Easier local testing and debugging
- Single deployment unit
- No Lambda cold start issues
- No API Gateway configuration overhead
- All pipeline logic in one codebase

The FastAPI server communicates with the same AWS services (S3, Bedrock, DynamoDB) using Boto3, identical to how the Lambda functions would.

### Frontend: Next.js

The design document specifies React 18.x. We use **Next.js** (which is built on React) as the frontend framework, gaining:

- File-based routing (no manual router setup)
- Server-side rendering for faster initial load
- Built-in API routes if needed
- Simplified deployment

---

## 2. AWS Services Used vs Deferred

### Services to BUILD

| # | AWS Service | Purpose in POC | Setup Effort |
|---|-------------|---------------|-------------|
| 1 | **Amazon S3** | 1 bucket: `kiranastudio` with prefixes `videos/`, `frames/`, `images/` | 15 min |
| 2 | **Amazon Bedrock** | Claude 3.5 Haiku (product detection) + Titan Image Gen v2 (studio images) | Model access request |
| 3 | **Amazon DynamoDB** | 2 tables: `Jobs`, `Catalogs` | 20 min |

### Non-AWS Tech to BUILD

| # | Technology | Purpose in POC |
|---|-----------|---------------|
| 1 | **FastAPI (Python 3.11)** | Backend server -- all API endpoints + pipeline logic |
| 2 | **Next.js** | Frontend -- upload, status, review, export screens |
| 3 | **OpenCV 4.8 + scikit-image** | Frame extraction + blur detection + SSIM dedup |
| 4 | **Boto3** | AWS SDK for S3, Bedrock, DynamoDB calls |
| 5 | **Axios** | HTTP client for frontend API calls |

### Services DEFERRED (explain in presentation)

| Service | Reason to Defer | Production Story |
|---------|----------------|-----------------|
| AWS Lambda | FastAPI server replaces all Lambda functions for POC | "In production, each pipeline step runs as an independent Lambda for scaling and fault isolation" |
| API Gateway | FastAPI handles routing directly | "API Gateway provides throttling, caching, and Cognito auth in production" |
| Step Functions | Sequential processing in FastAPI replaces orchestration | "Step Functions handles parallel processing + error recovery in production" |
| MediaConvert | OpenCV `cv2.VideoCapture` in FastAPI does the same at POC scale | "MediaConvert handles frame extraction at scale with managed transcoding" |
| OpenSearch Serverless | ~$700/month minimum, 1-2 days setup | "Hybrid cataloging with k-NN search reduces image generation cost by 60%" |
| Titan Embeddings | Only needed for OpenSearch similarity search | "Multimodal embeddings power the product matching system" |
| Cognito | Auth adds no demo value | "Cognito handles JWT auth with phone/email verification in production" |
| CloudFront | CDN not needed for demo | "CloudFront serves images with sub-100ms latency globally" |
| Amplify | Next.js can self-host or use Vercel | "Amplify provides CI/CD + custom domains in production" |
| Secrets Manager | Use environment variables for POC | "Secrets Manager handles credential rotation in production" |
| CloudWatch | Console logging is sufficient for POC | "CloudWatch dashboards monitor pipeline health in production" |

---

## 3. Architecture

```
+-----------------------------------------------------------+
|                  NEXT.JS APP                               |
|  +----------+  +--------------+  +----------------------+ |
|  | Upload   |  | Processing   |  | Product Review Grid  | |
|  | Screen   |  | Status       |  | + ONDC Export        | |
|  +----------+  +--------------+  +----------------------+ |
+------------------------+----------------------------------+
                         | Axios
                         v
              +---------------------+
              |   FASTAPI SERVER    |
              |   (Python 3.11)    |
              +----------+----------+
                         |
         +---------------+---------------+
         |               |               |
         v               v               v
   S3 Bucket       Bedrock (AI)    DynamoDB (Data)
   /videos/        - Claude 3.5    - Jobs table
   /frames/        - Titan ImgGen  - Catalogs table
   /images/
```

### Pipeline Flow Inside FastAPI

```
POST /api/v1/jobs/{video_id}/process
         |
         v
  Step 1: Download video from S3
         |
         v
  Step 2: Extract frames (OpenCV cv2.VideoCapture)
         |   Upload frames to S3 (frames/ prefix)
         v
  Step 3: Filter frames (Laplacian blur + SSIM dedup)
         |   Keep top 5 sharpest unique frames
         v
  Step 4: Detect products (Bedrock Claude 3.5 Haiku)
         |   Parse JSON response per frame
         v
  Step 5: Deduplicate products (brand+name+weight matching)
         |
         v
  Step 6: Generate studio images (Bedrock Titan Image Gen v2)
         |   Upload images to S3 (images/ prefix)
         v
  Step 7: Format ONDC/Beckn JSON
         |
         v
  Step 8: Save catalog to DynamoDB
         |
         v
  Return: { job_id, status: "COMPLETED", catalog_id }
```

---

## 4. FastAPI Endpoints

### 4.1 Upload Endpoints

**POST `/api/v1/upload/presigned-url`**

```
Request:  { "content_type": "video/mp4", "file_size": 15000000 }
Response: { "video_id": "uuid", "upload_url": "https://s3...", "expires_in": 300 }
```

Logic:
1. Generate UUID for video_id
2. Create presigned PUT URL for S3
3. Create job entry in DynamoDB Jobs table (status: UPLOADED)
4. Return presigned URL + video_id

---

### 4.2 Pipeline Endpoint

**POST `/api/v1/jobs/{video_id}/process`**

```
Request:  Path parameter: video_id
Response: { "job_id": "uuid", "status": "COMPLETED", "catalog_id": "uuid" }
```

Logic (sequential in a single endpoint, runs as a background task):

```
Step 1: EXTRACT FRAMES
  - Download video from S3
  - Use cv2.VideoCapture to extract 1 frame/sec
  - Upload frames to S3 (kiranastudio/frames/{video_id}/)
  - Update DynamoDB job status -> EXTRACTING

Step 2: FILTER FRAMES
  - Calculate Laplacian variance for each frame
  - Remove frames with blur_score < 100
  - Remove duplicate frames using SSIM (threshold 0.95)
  - Keep top 5 sharpest unique frames
  - Update DynamoDB job status -> FILTERING

Step 3: DETECT PRODUCTS
  - For each quality frame:
    - Base64 encode the image
    - Call Bedrock Claude 3.5 Haiku with detection prompt
    - Parse JSON response for products
  - Update DynamoDB job status -> DETECTING

Step 4: DEDUPLICATE
  - Merge products from all frames
  - Deduplicate by brand + product_name + net_weight (lowercase)
  - Update DynamoDB job status -> DEDUPLICATING

Step 5: GENERATE STUDIO IMAGES
  - For each unique product:
    - Call Bedrock Titan Image Gen v2 (OUTPAINTING mode)
    - Prompt: "Product on clean white studio background..."
    - Upload generated image to S3 (kiranastudio/images/{video_id}/)
    - If generation fails -> use original cropped image as fallback
  - Update DynamoDB job status -> GENERATING

Step 6: FORMAT ONDC
  - Transform products into ONDC/Beckn JSON schema
  - Include: descriptor, images, price (placeholder), quantity
  - Save complete catalog to DynamoDB Catalogs table
  - Update DynamoDB job status -> COMPLETED
```

Note: This endpoint triggers processing as a **FastAPI BackgroundTask** and returns immediately with the job_id. The frontend polls the status endpoint.

---

### 4.3 Status Endpoint

**GET `/api/v1/jobs/{video_id}/status`**

```
Request:  Path parameter: video_id
Response: { "job_id": "uuid", "status": "DETECTING", "product_count": 0 }
```

Logic:
1. Query DynamoDB Jobs table
2. Return current status + metadata

---

### 4.4 Catalog Endpoint

**GET `/api/v1/jobs/{video_id}/catalog`**

```
Request:  Path parameter: video_id
Response: Full ONDC catalog JSON + studio image URLs
```

Logic:
1. Query DynamoDB Jobs table for job status
2. If COMPLETED -> Query DynamoDB Catalogs table
3. Generate signed S3 URLs for studio images
4. Return catalog

---

### 4.5 Update Catalog Endpoint

**PUT `/api/v1/catalogs/{catalog_id}`**

```
Request:  { "products": [...updated products with prices...] }
Response: { "status": "updated", "catalog_id": "uuid" }
```

Logic:
1. Receive edited products from frontend (prices, corrections)
2. Update DynamoDB Catalogs table
3. Return success

---

## 5. DynamoDB Tables

### Table: `kiranastudio-jobs`

| Attribute | Type | Key |
|-----------|------|-----|
| job_id | String | Partition Key |
| video_id | String | -- |
| status | String | -- |
| created_at | String (ISO 8601) | -- |
| updated_at | String (ISO 8601) | -- |
| product_count | Number | -- |
| error_message | String | -- |

### Table: `kiranastudio-catalogs`

| Attribute | Type | Key |
|-----------|------|-----|
| catalog_id | String | Partition Key |
| job_id | String | -- |
| status | String (DRAFT/PUBLISHED) | -- |
| ondc_catalog | Map | -- |
| products | List | -- |
| created_at | String (ISO 8601) | -- |

---

## 6. S3 Buckets

| Bucket | Purpose | Lifecycle |
|--------|---------|-----------|
| `kiranastudio-videos` | Uploaded video files | Delete after 7 days |
| `kiranastudio-frames` | Extracted frame images | Delete after 24 hours |
| `kiranastudio-images` | Studio-generated product images | Indefinite |

---

## 7. Next.js Frontend Screens

### Screen 1: Upload Screen
- File input for video selection (or drag-and-drop)
- Video preview before upload
- Upload progress bar
- "Process" button to trigger pipeline

### Screen 2: Processing Status
- Real-time status display (polls `/api/v1/jobs/{video_id}/status` every 3 seconds)
- Status steps shown: Extracting -> Filtering -> Detecting -> Generating -> Formatting -> Complete
- Estimated time remaining

### Screen 3: Product Review Grid
- Grid of detected products with:
  - Studio image (from Titan Gen)
  - Brand name
  - Product name
  - Net weight
  - Variant
  - Price input field (editable)
- Edit button per product
- Delete button per product
- "Save Changes" button

### Screen 4: Catalog Export
- Preview of ONDC JSON structure
- "Download JSON" button
- Product count summary
- Total catalog value

### Frontend Tech:
- Next.js (React 18.x based)
- Axios for API calls
- React useState/useContext for state (skip Redux for POC simplicity)
- CSS Modules or plain CSS for styling

---

## 8. Bedrock Model Access

**Pre-requisite:** Request access to these models in `ap-south-1` (Mumbai):

| Model | Model ID | Access Request |
|-------|----------|---------------|
| Claude 3.5 Haiku | `anthropic.claude-3-5-haiku-20241022-v1:0` | Bedrock Console -> Model Access |
| Titan Image Gen v2 | `amazon.titan-image-generator-v2:0` | Bedrock Console -> Model Access |

Do this on Day 1. Model access approval can take a few hours.

---

## 9. Day-by-Day Execution Plan

### Day 1 (Feb 26) -- AWS Setup + FastAPI Scaffold + Upload Flow
**Goal:** All AWS resources created, video upload working end-to-end

| Task | Time | Details |
|------|------|---------|
| Request Bedrock model access (Claude + Titan) | 15 min | Do this FIRST, approval takes time |
| Create S3 bucket with prefixes | 10 min | kiranastudio bucket with videos/, frames/, images/ |
| Create 2 DynamoDB tables | 15 min | jobs, catalogs |
| Set up FastAPI project with dependencies | 1 hr | FastAPI, uvicorn, boto3, opencv, scikit-image |
| Code presigned URL endpoint | 1.5 hrs | POST /api/v1/upload/presigned-url |
| Test upload flow (Postman/curl) | 30 min | Upload a test video to S3 |
| Bootstrap Next.js app | 1 hr | npx create-next-app |
| Build Upload Screen UI | 2 hrs | File picker, progress bar, upload to S3 |

**Day 1 Deliverable:** Can upload a video from Next.js app -> S3

---

### Day 2 (Feb 27) -- Frame Extraction + Filtering
**Goal:** Video -> quality frames pipeline working

| Task | Time | Details |
|------|------|---------|
| Code frame extraction module (cv2.VideoCapture) | 2.5 hrs | Extract 1fps, upload frames to S3 |
| Code blur detection (Laplacian variance) | 1 hr | Threshold = 100 |
| Code duplicate detection (SSIM) | 1 hr | Threshold = 0.95 |
| Integrate into pipeline endpoint | 1.5 hrs | Steps 1+2 of pipeline |
| Test with real kirana shelf video | 1.5 hrs | Record a test video or find one online |
| Set up FastAPI BackgroundTask for async processing | 1 hr | Non-blocking pipeline |

**Day 2 Deliverable:** Upload video -> get 3-5 sharp, unique frames in S3

---

### Day 3 (Feb 28) -- Product Detection with Claude
**Goal:** Frames -> structured product JSON

| Task | Time | Details |
|------|------|---------|
| Verify Bedrock model access is approved | 15 min | Check console |
| Code Bedrock Claude 3.5 Haiku invocation | 2 hrs | Base64 encode image, structured prompt |
| Prompt engineering + testing | 2 hrs | Test with different shelf images, refine prompt |
| Code product deduplication | 1 hr | brand+name+weight matching |
| Integrate Steps 3+4 into pipeline | 1 hr | Detection + dedup |
| Code status endpoint | 1 hr | GET /api/v1/jobs/{video_id}/status |
| Test full pipeline: video -> products JSON | 1 hr | End-to-end test |

**Day 3 Deliverable:** Upload video -> get list of detected products with brand, name, weight, variant

---

### Day 4 (Mar 1) -- Studio Image Generation + ONDC Formatting
**Goal:** Products -> studio images + ONDC catalog

| Task | Time | Details |
|------|------|---------|
| Code Titan Image Gen v2 integration | 2 hrs | OUTPAINTING mode, white bg prompt |
| Test studio image generation quality | 1.5 hrs | Tune prompts for best output |
| Code fallback (use original crop if gen fails) | 30 min | Error handling |
| Code ONDC/Beckn JSON formatting | 2 hrs | Template from design doc section 4.9 |
| Save catalog to DynamoDB | 1 hr | Catalogs table write |
| Code catalog retrieval endpoint | 1 hr | GET /api/v1/jobs/{video_id}/catalog |
| Test complete pipeline end-to-end | 1 hr | Video -> ONDC catalog with studio images |

**Day 4 Deliverable:** Complete backend pipeline working -- video -> studio images -> ONDC catalog in DynamoDB

---

### Day 5 (Mar 2) -- Next.js Frontend: Status + Review + Edit
**Goal:** Functional product review dashboard

| Task | Time | Details |
|------|------|---------|
| Build Processing Status screen | 2 hrs | Polling job status, step progress indicators |
| Build Product Review Grid | 3 hrs | Product cards with studio images, all fields |
| Build Product Edit form | 1.5 hrs | Inline editing of name, weight, price |
| Build Delete product functionality | 30 min | Remove from catalog |
| Code update catalog endpoint | 1 hr | PUT /api/v1/catalogs/{catalog_id} |
| Connect frontend to all API endpoints | 1 hr | Axios integration |

**Day 5 Deliverable:** Can upload video -> see processing -> review products -> edit details

---

### Day 6 (Mar 3) -- Catalog Export + UI Polish
**Goal:** Complete user flow + polished UI

| Task | Time | Details |
|------|------|---------|
| Build ONDC JSON export/download | 1.5 hrs | Download as .json file |
| Build catalog summary view | 1 hr | Product count, total items |
| UI polish -- colors, typography, spacing | 2 hrs | Professional look |
| Loading states, error states, empty states | 1.5 hrs | User feedback |
| Mobile responsiveness | 1 hr | Works on phone browser |
| Add KiranaStudio branding/logo | 30 min | Header, favicon |

**Day 6 Deliverable:** Complete, polished web app with full user flow

---

### Day 7 (Mar 4) -- Deploy + Test + Demo Prep
**Goal:** Deployed prototype, recorded demo

| Task | Time | Details |
|------|------|---------|
| Deploy FastAPI to EC2 or any cloud VM | 1.5 hrs | uvicorn behind nginx or direct |
| Deploy Next.js (Vercel or S3 static export) | 1 hr | next build + deploy |
| End-to-end testing with 3+ different videos | 2 hrs | Test edge cases |
| Fix critical bugs | 2 hrs | Buffer time |
| Record demo video / prepare live demo | 1.5 hrs | Screen recording + narration |

**Day 7 Deliverable:** Live, deployed, tested prototype with demo ready

---

## 10. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bedrock model access delayed | Medium | High | Request on Day 1. Backup: use us-east-1 if ap-south-1 is slow |
| Pipeline takes too long for large videos | Medium | Medium | Limit to 10-sec videos, top 5 frames, max 10 products for image gen |
| Claude returns malformed JSON | Medium | Medium | Wrap in try/catch, retry once, use JSON repair |
| Titan Image Gen produces poor quality | Low | Low | Fallback to original cropped image. Tune prompt on Day 4 |
| Video format incompatible | Low | Low | Validate MP4 format on upload |
| FastAPI server memory issues with OpenCV | Low | Medium | Process one frame at a time, clean up after each |

---

## 11. What to Highlight in the Demo

When presenting this POC, emphasize these value propositions:

1. **"Zero-touch cataloging"** -- Shopkeeper just records a video, everything else is automated
2. **"AI-powered detection"** -- Claude 3.5 Haiku accurately extracts product details from shelf images
3. **"Studio-quality images"** -- Titan Image Gen transforms shelf photos into e-commerce-ready images
4. **"ONDC-ready"** -- Output is Beckn protocol compliant, ready for the ONDC network
5. **"Smart frame selection"** -- Not brute-force; we select the sharpest, most unique frames
6. **"Production-ready architecture"** -- Explain the full design (Step Functions, OpenSearch hybrid cataloging, Cognito auth, Lambda) as the production roadmap

---

## 12. Files and Directory Structure

```
kiranastudio/
|-- backend/
|   |-- app/
|   |   |-- main.py                 # FastAPI app entry point
|   |   |-- config.py               # AWS config, env vars
|   |   |-- routers/
|   |   |   |-- upload.py           # POST /upload/presigned-url
|   |   |   |-- jobs.py             # POST /jobs/{id}/process, GET /status
|   |   |   |-- catalogs.py         # GET catalog, PUT update, export
|   |   |-- services/
|   |   |   |-- s3_service.py       # S3 upload/download helpers
|   |   |   |-- dynamo_service.py   # DynamoDB read/write helpers
|   |   |   |-- bedrock_service.py  # Claude + Titan invocation
|   |   |-- pipeline/
|   |   |   |-- orchestrator.py     # Runs full pipeline sequentially
|   |   |   |-- frame_extractor.py  # OpenCV frame extraction
|   |   |   |-- frame_filter.py     # Blur detection + SSIM dedup
|   |   |   |-- product_detector.py # Claude 3.5 Haiku product detection
|   |   |   |-- deduplicator.py     # Product deduplication logic
|   |   |   |-- image_generator.py  # Titan Image Gen v2 studio images
|   |   |   |-- ondc_formatter.py   # ONDC/Beckn JSON formatting
|   |   |-- models/
|   |   |   |-- schemas.py          # Pydantic request/response models
|   |-- requirements.txt
|   |-- .env                        # AWS credentials, bucket names
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |   |-- page.jsx            # Home / Upload screen
|   |   |   |-- processing/
|   |   |   |   |-- [jobId]/
|   |   |   |       |-- page.jsx    # Processing status screen
|   |   |   |-- catalog/
|   |   |   |   |-- [catalogId]/
|   |   |   |       |-- page.jsx    # Product review + edit screen
|   |   |   |-- export/
|   |   |       |-- [catalogId]/
|   |   |           |-- page.jsx    # Catalog export screen
|   |   |-- components/
|   |   |   |-- UploadZone.jsx
|   |   |   |-- ProcessingSteps.jsx
|   |   |   |-- ProductGrid.jsx
|   |   |   |-- ProductCard.jsx
|   |   |   |-- ProductEditForm.jsx
|   |   |   |-- CatalogPreview.jsx
|   |   |-- services/
|   |   |   |-- api.js              # Axios API calls
|   |   |-- styles/
|   |       |-- globals.css
|   |-- package.json
|   |-- next.config.js
|-- PROTOTYPE_PLAN.md               # This file
|-- design.md                       # Original design document
|-- requirements.md                 # Original requirements document
```

---

## 13. Estimated Costs (POC Period)

| Service | Estimated Usage | Cost |
|---------|----------------|------|
| S3 (single bucket) | < 1 GB | ~$0.02 |
| DynamoDB | < 25 GB, < 200M requests | Free tier |
| Bedrock Claude 3.5 Haiku | ~100 invocations | ~$1-2 |
| Bedrock Titan Image Gen | ~50 images x $0.008/image | ~$0.40 |
| EC2 (t3.micro for FastAPI) | 7 days | Free tier eligible |
| **Total** | | **~$2-3** |

---

**Document Version:** 1.1  
**Author:** Team MotherBoard  
**Created:** February 25, 2026  
**Updated:** February 26, 2026
