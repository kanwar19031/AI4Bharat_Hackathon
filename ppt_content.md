# KiranaStudio - Presentation Content
## Team MotherBoard | Theme: AI for Retail and Commerce

---

## SLIDE 1: Title Slide

**Team Name:** MotherBoard

**Problem Statement:** Zero-Touch ONDC Onboarding for Kirana Stores via Video-Based Catalog Creation

**Team Leader:** Kanwarraj Singh

---

## SLIDE 2: Brief About the Idea

### The Problem

India has over 12 million kirana stores, yet fewer than 5% are digitally enabled. The primary barrier is not technology access but **catalog creation complexity**. A typical kirana store stocks 500-2000 SKUs. Manually entering each product with name, price, weight, and image into ONDC-compliant formats takes 3-5 days of dedicated effort.

**Current Reality:**
- 200,000+ kirana stores closed in 2024 due to quick-commerce competition [Source: Economic Times, Dec 2024]
- 60% of Mumbai kiranas reported declining sales directly attributed to quick-commerce platforms [Source: JP Morgan Study, 2024]
- ONDC has onboarded 300,000+ sellers, but adoption remains slow due to complex onboarding [Source: ONDC Annual Report]

### Our Solution: KiranaStudio

**KiranaStudio** transforms a 10-second video of a shop shelf into a complete, ONDC-ready digital catalog with studio-quality product images - requiring zero typing from the shopkeeper.

**Core Innovation:**
A shopkeeper simply pans their phone camera across their shelves. Our GenAI pipeline automatically:
1. Extracts the sharpest frames from the video
2. Detects and identifies every product visible
3. Reads product labels (brand, name, weight, variant)
4. Generates professional studio-quality images
5. Outputs ONDC-compliant JSON catalog

**One video. One minute. Complete digital store.**

---

## SLIDE 3: Solution Differentiation

### How is KiranaStudio Different from Existing Solutions?

| Aspect | Existing Solutions | KiranaStudio |
|--------|-------------------|--------------|
| **Input Method** | Static photos or manual entry | Video capture (natural scanning motion) |
| **Image Quality** | Original photos (cluttered backgrounds) | GenAI studio-quality images (white background) |
| **ONDC Compliance** | Requires manual formatting | Native ONDC/Beckn protocol JSON output |
| **Technical Barrier** | Requires training or literacy | Zero-typing, WhatsApp-like simplicity |
| **Cost Model** | Per-product or subscription fees | Hybrid cataloging reduces GenAI costs by 60% |

**Reference - Existing Players:**
- InfiBrAIn by Infilect: Enterprise-focused, static image input, no ONDC integration [infilect.com]
- BlinkShelf by Microblink: Real-time recognition but no studio image generation [microblink.com]
- Google Shelf Checking AI: SAP ERP integration focus, not designed for small retailers [cloud.google.com/blog]

### How Will It Solve the Problem?

1. **Eliminates Manual Data Entry**: Video-to-catalog automation reduces onboarding from days to minutes
2. **Professional Presentation**: GenAI-generated studio images make kirana products visually competitive with e-commerce listings
3. **ONDC-Ready Output**: Direct integration with ONDC network without intermediate formatting
4. **Cost-Optimized**: Hybrid cataloging reuses existing product images, invoking GenAI only for new/unique items

### Unique Selling Proposition (USP)

**"Shelf-to-Shop in 60 Seconds"**

The only solution that combines:
- Video-based input (not static images)
- GenAI studio image generation (professional product photography)
- Native ONDC protocol compliance
- Intelligent cost optimization through product similarity matching
- 100% AWS-native serverless architecture

---

## SLIDE 4: List of Features

### Core Features

**1. Smart Video Capture**
- Landscape-mode camera interface with stabilization guide
- Real-time feedback on video quality
- Supports 10-30 second shelf scanning videos
- Works with standard smartphone cameras (no special hardware)

**2. Intelligent Frame Selection**
- Automatic blur detection using Laplacian variance algorithm
- Duplicate frame elimination using SSIM (Structural Similarity Index)
- Reduces 300 raw frames to 3-5 high-quality frames for processing
- Reference: PyImageSearch blur detection methodology [pyimagesearch.com/2015/09/07/blur-detection-with-opencv]

**3. AI-Powered Product Detection**
- Vision-Language Model (Claude 3.5 Haiku) analyzes shelf images
- Extracts: Brand name, Product name, Net weight, Variant type
- Handles multiple products per frame
- Ignores partially visible or cut-off items
- Outputs structured JSON (not conversational text)

**4. Hybrid Cataloging System**
- Generates vector embeddings for each detected product using Amazon Titan Multimodal Embeddings
- Queries existing product database using k-NN similarity search
- If match found (similarity > 0.92): Reuses existing studio image
- If no match: Generates new studio image via Titan Image Generator
- Reduces GenAI image generation costs by up to 60%

**5. Studio Image Generation**
- Automatic background removal from original product crop
- Generation of clean white studio background with soft lighting
- Consistent image dimensions and formatting
- Reference: Amazon Titan Image Generator v2 capabilities [docs.aws.amazon.com/bedrock]

**6. ONDC-Compliant Output**
- Generates catalog in Beckn Protocol JSON schema
- Includes all required fields: descriptor, price, images, fulfillment
- Ready for direct upload to any ONDC seller application
- Reference: ONDC Retail Protocol Specifications [github.com/ONDC-Official/ONDC-Protocol-Specs]

**7. Trust-But-Verify Editor**
- Post-processing interface shows grid of detected products
- Shopkeeper can tap to edit/correct any field
- **Price entry is mandatory** (AI cannot guess selling price)
- Approve/reject individual products before final catalog generation

**8. Fail-Safe Mechanisms**
- If GenAI image generation fails: Falls back to cropped original image
- If product detection confidence < 70%: Flags for manual review
- Never shows blank spaces in final catalog

### Visual Feature Map

```
[VIDEO CAPTURE] --> [FRAME SELECTION] --> [PRODUCT DETECTION]
                                                   |
                                                   v
[ONDC CATALOG] <-- [VERIFY/EDIT] <-- [STUDIO IMAGES] <-- [HYBRID CHECK]
```

---

## SLIDE 5: Process Flow Diagram

### End-to-End User Journey

```
+------------------+
|   SHOPKEEPER     |
|   opens app      |
+--------+---------+
         |
         v
+------------------+
| VIDEO CAPTURE    |
| - Landscape mode |
| - 10-30 seconds  |
| - Shelf scanning |
+--------+---------+
         |
         v
+------------------+
| UPLOAD TO CLOUD  |
| - S3 presigned   |
|   URL upload     |
| - Progress bar   |
+--------+---------+
         |
         v
+------------------+
| FRAME EXTRACTION |
| - MediaConvert   |
| - 1 frame/sec    |
+--------+---------+
         |
         v
+------------------+
| QUALITY FILTER   |
| - Blur detection |
| - Deduplication  |
| - 3-5 frames out |
+--------+---------+
         |
         v
+------------------+
| PRODUCT DETECT   |
| - Claude 3.5     |
|   Haiku VLM      |
| - JSON output    |
+--------+---------+
         |
         v
+------------------+
| HYBRID CATALOG   |
| - Embedding gen  |
| - Similarity     |
|   search         |
| - Reuse or Gen   |
+--------+---------+
         |
         v
+------------------+
| STUDIO IMAGES    |
| - Titan Image    |
|   Generator      |
| - White BG       |
+--------+---------+
         |
         v
+------------------+
| VERIFY & EDIT    |
| - Review grid    |
| - Add prices     |
| - Approve items  |
+--------+---------+
         |
         v
+------------------+
| ONDC CATALOG     |
| - Beckn JSON     |
| - Ready to       |
|   publish        |
+------------------+
```

### Use Case Diagram

**Primary Actor:** Kirana Shopkeeper

**Use Cases:**
1. UC1: Capture shelf video
2. UC2: Upload video for processing
3. UC3: View processing status
4. UC4: Review detected products
5. UC5: Edit product details (especially price)
6. UC6: Approve/reject products
7. UC7: Download ONDC-ready catalog
8. UC8: Re-scan specific shelf sections

**Secondary Actor:** System (KiranaStudio Pipeline)

**System Use Cases:**
1. SUC1: Extract quality frames from video
2. SUC2: Detect and identify products
3. SUC3: Check product similarity against existing database
4. SUC4: Generate studio images for new products
5. SUC5: Format catalog to ONDC specifications

---

## SLIDE 6: Wireframes/Mock Diagrams (Optional)

### Screen 1: Home/Capture Screen

```
+--------------------------------+
|  KiranaStudio                  |
|  [=] Menu                      |
+--------------------------------+
|                                |
|  +------------------------+    |
|  |                        |    |
|  |    CAMERA VIEWFINDER   |    |
|  |    (Landscape Mode)    |    |
|  |                        |    |
|  |  - - - - - - - - - - - |    |
|  |  ^ Stabilization Guide |    |
|  |                        |    |
|  +------------------------+    |
|                                |
|  "Pan slowly across shelf"     |
|                                |
|  [    START RECORDING    ]     |
|                                |
|  Recent Scans:                 |
|  [Shelf A] [Shelf B] [+]       |
|                                |
+--------------------------------+
```

### Screen 2: Processing Status

```
+--------------------------------+
|  Processing Your Video         |
+--------------------------------+
|                                |
|  Video uploaded successfully   |
|  [====================] 100%   |
|                                |
|  Extracting frames...          |
|  [==============      ]  70%   |
|                                |
|  Status: Analyzing products    |
|                                |
|  Products found so far: 12     |
|                                |
|  Estimated time: 45 seconds    |
|                                |
+--------------------------------+
```

### Screen 3: Product Review Grid

```
+--------------------------------+
|  Review Products (24 found)    |
+--------------------------------+
| +------+ +------+ +------+     |
| |[IMG] | |[IMG] | |[IMG] |     |
| |Parle | |Maggi | |Surf  |     |
| |G 100g| |2-min | |Excel |     |
| |Rs.__ | |Rs.__ | |Rs.__ |     |
| |[Edit]| |[Edit]| |[Edit]|     |
| +------+ +------+ +------+     |
|                                |
| +------+ +------+ +------+     |
| |[IMG] | |[IMG] | |[IMG] |     |
| |Dairy | |Britan| |Coca  |     |
| |Milk  | |nia   | |Cola  |     |
| |Rs.__ | |Rs.__ | |Rs.__ |     |
| |[Edit]| |[Edit]| |[Edit]|     |
| +------+ +------+ +------+     |
|                                |
| [SELECT ALL] [GENERATE CATALOG]|
+--------------------------------+
```

### Screen 4: Product Edit Modal

```
+--------------------------------+
|  Edit Product Details          |
|                           [X]  |
+--------------------------------+
|  +--------+                    |
|  | [IMG]  |  Brand: Parle      |
|  | Studio |  [_______________] |
|  | Image  |                    |
|  +--------+  Product: Parle-G  |
|              [_______________] |
|                                |
|              Weight: 100g      |
|              [_______________] |
|                                |
|              Price (Rs.)*      |
|              [_______________] |
|              * Required field  |
|                                |
|  [DELETE]          [SAVE]      |
+--------------------------------+
```

---

## SLIDE 7: Architecture Diagram

### High-Level AWS Architecture

```
                                    +------------------+
                                    |   MOBILE APP     |
                                    | (React Native/   |
                                    |  Amplify)        |
                                    +--------+---------+
                                             |
                                             | HTTPS
                                             v
+-----------------------------------------------------------------------------------+
|                              AWS CLOUD                                             |
+-----------------------------------------------------------------------------------+
|                                                                                    |
|  +----------------+     +------------------+     +--------------------+            |
|  | API GATEWAY    |---->| LAMBDA           |---->| S3 BUCKET          |            |
|  | (REST API)     |     | (Presigned URL   |     | (Video Storage)    |            |
|  +----------------+     |  Generator)      |     +----------+---------+            |
|                         +------------------+                |                      |
|                                                             | S3 Event            |
|                                                             v                      |
|  +------------------------------------------------------------------------+       |
|  |                     AWS STEP FUNCTIONS                                  |       |
|  |                     (Pipeline Orchestrator)                             |       |
|  +------------------------------------------------------------------------+       |
|       |                    |                    |                    |             |
|       v                    v                    v                    v             |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
|  | STATE 1   |      | STATE 2   |      | STATE 3   |      | STATE 4   |           |
|  | Media     |      | Lambda    |      | Bedrock   |      | Lambda    |           |
|  | Convert   |      | Frame     |      | Claude    |      | Dedup     |           |
|  | (Extract  |      | Filter    |      | 3.5 Haiku |      | Products  |           |
|  |  Frames)  |      | (OpenCV)  |      | (Detect)  |      |           |           |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
|                                                                  |                 |
|       +----------------------------------------------------------+                 |
|       |                                                                            |
|       v                                                                            |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
|  | STATE 5   |      | STATE 6   |      | STATE 7   |      | STATE 8   |           |
|  | Bedrock   |      | OpenSearch|      | Bedrock   |      | Lambda    |           |
|  | Titan     |      | Serverless|      | Titan     |      | Format    |           |
|  | Embed     |      | (k-NN     |      | Image Gen |      | ONDC JSON |           |
|  | (Vector)  |      |  Search)  |      | (Studio)  |      |           |           |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
|                            |                                      |                |
|                            v                                      v                |
|                     +-----------+                          +-----------+           |
|                     | OpenSearch|                          | DynamoDB  |           |
|                     | Serverless|                          | (Catalog  |           |
|                     | (Product  |                          |  Storage) |           |
|                     |  Vectors) |                          +-----------+           |
|                     +-----------+                                                  |
|                                                                                    |
+-----------------------------------------------------------------------------------+
```

### Data Flow Summary

| Step | Service | Input | Output |
|------|---------|-------|--------|
| 1 | S3 | Video file (MP4) | Stored video |
| 2 | MediaConvert | Video | JPEG frames (1/sec) |
| 3 | Lambda + OpenCV | All frames | 3-5 quality frames |
| 4 | Bedrock Claude | Quality frames | Product JSON array |
| 5 | Lambda | Product JSON | Deduplicated products |
| 6 | Bedrock Titan Embed | Product crops | 1024-dim vectors |
| 7 | OpenSearch Serverless | Query vectors | Match results |
| 8 | Bedrock Titan Image | New products | Studio images |
| 9 | Lambda | All data | ONDC Beckn JSON |
| 10 | DynamoDB | Final catalog | Persistent storage |

### AWS Service References

- Step Functions + Bedrock: [aws.amazon.com/blogs/machine-learning/orchestrate-generative-ai-workflows-with-amazon-bedrock-and-aws-step-functions]
- MediaConvert Frame Capture: [docs.aws.amazon.com/mediaconvert/latest/ug/file-group-with-frame-capture-output.html]
- OpenSearch Serverless Vector: [docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html]
- Titan Multimodal Embeddings: [docs.aws.amazon.com/bedrock/latest/userguide/titan-multiemb-models.html]

---

## SLIDE 8: Technologies to be Used

### Complete Technology Stack

| Layer | Technology | Version/Model | Purpose |
|-------|------------|---------------|---------|
| **Mobile App** | React Native | 0.73+ | Cross-platform mobile app |
| **Web App** | React | 18.x | Web dashboard |
| **Hosting** | AWS Amplify | Latest | Frontend hosting and CI/CD |
| **API** | Amazon API Gateway | REST | Secure API endpoints |
| **Compute** | AWS Lambda | Python 3.11 | Serverless functions |
| **Orchestration** | AWS Step Functions | Standard | Pipeline state machine |
| **Video Processing** | AWS MediaConvert | Latest | Frame extraction |
| **Object Storage** | Amazon S3 | Standard | Video and image storage |
| **Frame Analysis** | OpenCV | 4.8+ | Blur detection, SSIM |
| **Vision AI** | Claude 3.5 Haiku | via Bedrock | Product detection and OCR |
| **Embeddings** | Titan Multimodal Embeddings G1 | via Bedrock | Product vector generation |
| **Vector Search** | Amazon OpenSearch Serverless | Latest | k-NN similarity search |
| **Image Generation** | Titan Image Generator v2 | via Bedrock | Studio image creation |
| **Database** | Amazon DynamoDB | On-demand | Catalog and job storage |
| **Authentication** | Amazon Cognito | Latest | User authentication |
| **Monitoring** | Amazon CloudWatch | Latest | Logs and metrics |

### Key Libraries and Frameworks

| Library | Purpose | Reference |
|---------|---------|-----------|
| OpenCV (cv2) | Image processing, blur detection | [docs.opencv.org] |
| scikit-image | SSIM calculation for frame deduplication | [scikit-image.org] |
| Boto3 | AWS SDK for Python | [boto3.amazonaws.com] |
| Pillow | Image manipulation | [pillow.readthedocs.io] |

### Why This Stack?

**1. 100% AWS Native**
- Single cloud provider simplifies security, billing, and compliance
- Seamless service integration via IAM roles
- Enterprise-grade SLAs and support

**2. Serverless-First**
- Zero server management overhead
- Pay-per-use pricing model
- Auto-scaling from 0 to millions of requests

**3. GenAI via Bedrock**
- No model hosting or GPU management
- Access to latest foundation models
- Built-in responsible AI guardrails

**4. Production-Ready**
- All services are GA (Generally Available)
- Multi-AZ redundancy by default
- SOC 2, ISO 27001, HIPAA compliant

---

## SLIDE 9: Estimated Implementation Cost

### Per-Catalog Generation Cost

| Component | AWS Service | Unit Pricing | Est. Cost per Video |
|-----------|-------------|--------------|---------------------|
| Video Upload | S3 Storage | $0.023/GB | Rs. 0.10 |
| Frame Extraction | MediaConvert | $0.015/min | Rs. 0.20 |
| Frame Processing | Lambda | $0.0000166/GB-sec | Rs. 0.50 |
| Product Detection | Claude 3.5 Haiku | $0.80/M input tokens | Rs. 2.00 |
| Embedding Generation | Titan Embed | $0.0008/image | Rs. 0.40 |
| Similarity Search | OpenSearch Serverless | $0.24/OCU-hr | Rs. 0.30 |
| Studio Image Gen | Titan Image Gen | $0.008/image | Rs. 3.00 (avg 5 new) |
| Database Write | DynamoDB | $1.25/M writes | Rs. 0.05 |
| **TOTAL** | | | **Rs. 6-8 per catalog** |

### Monthly Infrastructure Cost (Base)

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| OpenSearch Serverless | 2 OCU minimum | $350 (~Rs. 29,000) |
| API Gateway | Pay per request | Variable |
| Lambda | Pay per invocation | Variable |
| S3 Storage | Per GB stored | Variable |
| DynamoDB | On-demand | Variable |
| **Base Monthly** | | **~Rs. 30,000** |

### Cost Optimization Strategies

**1. Hybrid Cataloging**
- Reusing existing product images reduces Titan Image Gen calls by 60%
- Estimated savings: Rs. 2-3 per catalog

**2. Provisioned Throughput (at scale)**
- Bedrock provisioned capacity offers 15-30% discount for stable workloads
- Reference: [aws.amazon.com/bedrock/pricing]

**3. Reserved Capacity**
- OpenSearch Serverless reserved OCUs for predictable costs

### ROI Analysis

| Metric | Manual Catalog | KiranaStudio |
|--------|----------------|--------------|
| Time per catalog | 3-5 days | 2 minutes |
| Cost per catalog | Rs. 500+ (labor) | Rs. 6-8 |
| Image quality | Phone photos | Studio quality |
| ONDC compliance | Manual formatting | Automatic |

---

## SLIDE 10: Additional Information

### Scalability Considerations

**Current Design Supports:**
- 10,000+ concurrent video uploads
- 1 million+ product database for similarity matching
- Multi-region deployment capability

**Future Roadmap:**
1. **Multi-language Support**: Hindi, Tamil, Telugu labels using multilingual OCR
2. **Offline Mode**: On-device processing for Tier 3/4 cities with poor connectivity
3. **Category Expansion**: Beyond FMCG to electronics, apparel, hardware
4. **Bulk Operations**: Process multiple shelves in single batch job
5. **Analytics Dashboard**: Sales insights from catalog data

### ONDC Integration Details

**Supported ONDC Fields:**
- descriptor (name, short_desc, long_desc, images)
- price (currency, value, maximum_value)
- quantity (available, maximum)
- category_id (as per ONDC taxonomy)
- fulfillment_id (pickup, delivery options)

**Reference:** Beckn Protocol Specification [developers.becknprotocol.io/docs/introduction/beckn-protocol-specification]

### Security and Compliance

| Aspect | Implementation |
|--------|----------------|
| Data Encryption | S3 SSE, DynamoDB encryption at rest |
| Transit Security | TLS 1.2+ for all API calls |
| Authentication | Amazon Cognito with MFA option |
| Authorization | IAM roles with least privilege |
| Audit Logging | CloudTrail enabled |
| Data Residency | Mumbai region (ap-south-1) |

### Team Readiness

**Team MotherBoard** is prepared to:
1. Complete MVP development within hackathon timeline
2. Demonstrate end-to-end video-to-catalog workflow
3. Show ONDC-compliant JSON output
4. Present cost optimization via hybrid cataloging

### References and Resources

| Topic | Resource |
|-------|----------|
| Blur Detection | pyimagesearch.com/2015/09/07/blur-detection-with-opencv |
| SSIM Algorithm | scikit-image.org/docs/stable/api/skimage.metrics.html |
| Step Functions + Bedrock | aws.amazon.com/blogs/machine-learning/orchestrate-generative-ai-workflows-with-amazon-bedrock-and-aws-step-functions |
| Titan Multimodal Embeddings | docs.aws.amazon.com/bedrock/latest/userguide/titan-multiemb-models.html |
| OpenSearch Vector Search | docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html |
| MediaConvert Frame Capture | docs.aws.amazon.com/mediaconvert/latest/ug/file-group-with-frame-capture-output.html |
| ONDC Protocol | github.com/ONDC-Official/ONDC-Protocol-Specs |
| Beckn Protocol | developers.becknprotocol.io |

---

## END OF PRESENTATION CONTENT
