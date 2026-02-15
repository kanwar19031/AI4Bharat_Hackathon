# KiranaStudio - System Design Document

**Project:** KiranaStudio - Video-Based Catalog Generation Pipeline  
**Team:** MotherBoard  
**Version:** 1.0  
**Last Updated:** February 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture Design](#3-architecture-design)
4. [Component Details](#4-component-details)
5. [Data Flow](#5-data-flow)
6. [Database Design](#6-database-design)
7. [API Design](#7-api-design)
8. [Algorithm Details](#8-algorithm-details)
9. [Security Design](#9-security-design)
10. [Scalability Considerations](#10-scalability-considerations)
11. [Error Handling](#11-error-handling)
12. [References](#12-references)

---

## 1. Executive Summary

KiranaStudio is a serverless GenAI pipeline that transforms video recordings of retail shelves into ONDC-compliant digital catalogs with studio-quality product images. The system is designed to be:

- **Zero-touch**: No manual data entry required from shopkeepers
- **Cost-optimized**: Hybrid cataloging reduces GenAI costs by 60%
- **Scalable**: Serverless architecture handles variable loads
- **Compliant**: Native ONDC/Beckn protocol output

---

## 2. System Overview

### 2.1 High-Level Components

```
+-------------------+     +-------------------+     +-------------------+
|   CLIENT LAYER    |     |   API LAYER       |     |   PROCESSING      |
|                   |     |                   |     |   LAYER           |
| - Mobile App      |---->| - API Gateway     |---->| - Step Functions  |
| - Web Dashboard   |     | - Lambda (API)    |     | - Lambda (Compute)|
|                   |     | - Cognito (Auth)  |     | - MediaConvert    |
+-------------------+     +-------------------+     +-------------------+
                                                             |
                                                             v
+-------------------+     +-------------------+     +-------------------+
|   STORAGE LAYER   |     |   AI LAYER        |     |   SEARCH LAYER    |
|                   |     |                   |     |                   |
| - S3 (Videos)     |<----| - Bedrock Claude  |---->| - OpenSearch      |
| - S3 (Images)     |     | - Titan Embed     |     |   Serverless      |
| - DynamoDB        |     | - Titan Image Gen |     |   (Vector k-NN)   |
+-------------------+     +-------------------+     +-------------------+
```

### 2.2 Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cloud Provider | AWS | Hackathon requirement, comprehensive GenAI services |
| Architecture Style | Serverless | Zero ops overhead, pay-per-use, auto-scaling |
| Orchestration | Step Functions | Visual workflow, error handling, parallel processing |
| Video Processing | MediaConvert | Managed service, frame extraction built-in |
| Vision AI | Claude 3.5 Haiku | Best price/performance for multimodal tasks |
| Vector DB | OpenSearch Serverless | Managed k-NN, integrates with Bedrock |
| Image Generation | Titan Image Gen v2 | AWS native, background removal support |

---

## 3. Architecture Design

### 3.1 AWS Architecture Diagram

```
                              INTERNET
                                  |
                                  v
                        +------------------+
                        |   CloudFront     |
                        |   (CDN)          |
                        +--------+---------+
                                 |
                 +---------------+---------------+
                 |                               |
                 v                               v
        +----------------+              +----------------+
        |   Amplify      |              |  API Gateway   |
        |   (Frontend)   |              |  (REST API)    |
        +----------------+              +-------+--------+
                                                |
                                                v
                                       +----------------+
                                       |   Cognito      |
                                       |   (Auth)       |
                                       +-------+--------+
                                                |
                 +------------------------------+------------------------------+
                 |                              |                              |
                 v                              v                              v
        +----------------+             +----------------+             +----------------+
        | Lambda:        |             | Lambda:        |             | Lambda:        |
        | GetPresignedURL|             | GetJobStatus   |             | GetCatalog     |
        +-------+--------+             +-------+--------+             +-------+--------+
                |                              |                              |
                v                              v                              v
        +----------------+             +----------------+             +----------------+
        |   S3 Bucket    |             |   DynamoDB     |             |   DynamoDB     |
        |   (Videos)     |             |   (Jobs Table) |             |   (Catalog)    |
        +-------+--------+             +----------------+             +----------------+
                |
                | S3 Event Notification
                v
        +------------------+
        |  Step Functions  |
        |  State Machine   |
        +--------+---------+
                 |
    +------------+------------+------------+------------+
    |            |            |            |            |
    v            v            v            v            v
+--------+  +--------+  +--------+  +--------+  +--------+
|State 1 |  |State 2 |  |State 3 |  |State 4 |  |State 5 |
|Media   |->|Frame   |->|Product |->|Dedup   |->|Embed   |
|Convert |  |Filter  |  |Detect  |  |        |  |Gen     |
+--------+  +--------+  +--------+  +--------+  +--------+
                                                    |
                        +---------------------------+
                        |
    +-------------------+-------------------+
    |                                       |
    v                                       v
+--------+                             +--------+
|State 6 |                             |State 7 |
|Similar |                             |Image   |
|Search  |                             |Gen     |
+--------+                             +--------+
    |                                       |
    v                                       v
+------------------+                +------------------+
|   OpenSearch     |                |   S3 Bucket      |
|   Serverless     |                |   (Images)       |
+------------------+                +------------------+
                        |
                        v
                   +--------+
                   |State 8 |
                   |Format  |
                   |ONDC    |
                   +--------+
                        |
                        v
                +------------------+
                |   DynamoDB       |
                |   (Catalog)      |
                +------------------+
```

### 3.2 Step Functions State Machine

```json
{
  "Comment": "KiranaStudio Video-to-Catalog Pipeline",
  "StartAt": "ExtractFrames",
  "States": {
    "ExtractFrames": {
      "Type": "Task",
      "Resource": "arn:aws:states:::mediaconvert:createJob.sync",
      "Next": "FilterFrames"
    },
    "FilterFrames": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:ACCOUNT:function:FilterFrames",
      "Next": "DetectProducts"
    },
    "DetectProducts": {
      "Type": "Map",
      "ItemsPath": "$.qualityFrames",
      "MaxConcurrency": 5,
      "Iterator": {
        "StartAt": "InvokeClaude",
        "States": {
          "InvokeClaude": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "End": true
          }
        }
      },
      "Next": "DeduplicateProducts"
    },
    "DeduplicateProducts": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:ACCOUNT:function:DeduplicateProducts",
      "Next": "GenerateEmbeddings"
    },
    "GenerateEmbeddings": {
      "Type": "Map",
      "ItemsPath": "$.products",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "InvokeTitanEmbed",
        "States": {
          "InvokeTitanEmbed": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "End": true
          }
        }
      },
      "Next": "SimilaritySearch"
    },
    "SimilaritySearch": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:ACCOUNT:function:SimilaritySearch",
      "Next": "GenerateStudioImages"
    },
    "GenerateStudioImages": {
      "Type": "Map",
      "ItemsPath": "$.newProducts",
      "MaxConcurrency": 3,
      "Iterator": {
        "StartAt": "InvokeTitanImage",
        "States": {
          "InvokeTitanImage": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "End": true
          }
        }
      },
      "Next": "FormatONDC"
    },
    "FormatONDC": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-1:ACCOUNT:function:FormatONDC",
      "Next": "SaveCatalog"
    },
    "SaveCatalog": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "End": true
    }
  }
}
```

Reference: AWS Step Functions Developer Guide [docs.aws.amazon.com/step-functions/latest/dg/welcome.html]

---

## 4. Component Details

### 4.1 Video Upload Service

**Purpose:** Secure video upload from mobile devices to S3

**Implementation:**
```python
# Lambda: GeneratePresignedURL
import boto3
import uuid

def handler(event, context):
    s3_client = boto3.client('s3')
    video_id = str(uuid.uuid4())
    
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'kiranastudio-videos',
            'Key': f'uploads/{video_id}.mp4',
            'ContentType': 'video/mp4'
        },
        ExpiresIn=300  # 5 minutes
    )
    
    return {
        'video_id': video_id,
        'upload_url': presigned_url
    }
```

**Why Presigned URLs:**
- Client uploads directly to S3 (no server bottleneck)
- Secure (URL expires after 5 minutes)
- Cost-effective (no Lambda invocation for large uploads)

Reference: AWS S3 Presigned URLs [docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html]

### 4.2 Frame Extraction Service

**Purpose:** Extract frames from uploaded video

**AWS MediaConvert Job Configuration:**
```json
{
  "OutputGroups": [
    {
      "Name": "Frame Capture",
      "OutputGroupSettings": {
        "Type": "FILE_GROUP_SETTINGS",
        "FileGroupSettings": {
          "Destination": "s3://kiranastudio-frames/"
        }
      },
      "Outputs": [
        {
          "ContainerSettings": {
            "Container": "RAW"
          },
          "VideoDescription": {
            "CodecSettings": {
              "Codec": "FRAME_CAPTURE",
              "FrameCaptureSettings": {
                "FramerateNumerator": 1,
                "FramerateDenominator": 1,
                "MaxCaptures": 30,
                "Quality": 80
              }
            }
          }
        }
      ]
    }
  ]
}
```

Reference: MediaConvert Frame Capture [docs.aws.amazon.com/mediaconvert/latest/ug/file-group-with-frame-capture-output.html]

### 4.3 Frame Filter Service

**Purpose:** Remove blurry and duplicate frames

**Implementation:**
```python
# Lambda: FilterFrames
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def calculate_blur_score(image_bytes):
    """
    Calculate Laplacian variance as blur metric.
    Higher variance = sharper image.
    Reference: pyimagesearch.com/2015/09/07/blur-detection-with-opencv
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var

def is_duplicate(img1_bytes, img2_bytes, threshold=0.95):
    """
    Check if two images are duplicates using SSIM.
    Reference: scikit-image.org/docs/stable/api/skimage.metrics.html
    """
    img1 = cv2.imdecode(np.frombuffer(img1_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imdecode(np.frombuffer(img2_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    
    # Resize to same dimensions
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    similarity = ssim(img1, img2)
    return similarity > threshold

def handler(event, context):
    frames = event['frames']  # List of S3 keys
    
    # Stage 1: Filter by blur score
    BLUR_THRESHOLD = 100
    sharp_frames = []
    for frame_key in frames:
        image_bytes = get_from_s3(frame_key)
        blur_score = calculate_blur_score(image_bytes)
        if blur_score > BLUR_THRESHOLD:
            sharp_frames.append({
                'key': frame_key,
                'blur_score': blur_score,
                'bytes': image_bytes
            })
    
    # Stage 2: Remove duplicates
    unique_frames = []
    for frame in sharp_frames:
        is_dup = False
        for existing in unique_frames:
            if is_duplicate(frame['bytes'], existing['bytes']):
                is_dup = True
                break
        if not is_dup:
            unique_frames.append(frame)
    
    # Return top 5 sharpest unique frames
    unique_frames.sort(key=lambda x: x['blur_score'], reverse=True)
    return {
        'qualityFrames': [f['key'] for f in unique_frames[:5]]
    }
```

### 4.4 Product Detection Service

**Purpose:** Extract product information from shelf images using VLM

**Claude 3.5 Haiku Prompt:**
```
Analyze this retail shelf image and extract all visible products.

Return ONLY a valid JSON array with no additional text. Each product object must have:
- brand: The brand name (e.g., "Parle", "Maggi", "Surf Excel")
- product_name: Full product name including variant
- net_weight: Weight/volume with unit (e.g., "100g", "500ml")
- variant: Variant type if applicable (e.g., "Original", "Masala", "Lemon")

Rules:
1. Only include products that are fully visible
2. Ignore products that are cut off or partially visible
3. If a field is not readable, use null
4. Do not include duplicate products

Example output:
[
  {"brand": "Parle", "product_name": "Parle-G", "net_weight": "100g", "variant": null},
  {"brand": "Maggi", "product_name": "Maggi 2-Minute Noodles", "net_weight": "70g", "variant": "Masala"}
]
```

**Bedrock API Call:**
```python
import boto3
import json
import base64

def invoke_claude(image_bytes):
    bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode('utf-8')
                        }
                    },
                    {
                        "type": "text",
                        "text": PRODUCT_DETECTION_PROMPT
                    }
                ]
            }
        ]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-haiku-20241022-v1:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    products = json.loads(result['content'][0]['text'])
    return products
```

Reference: Amazon Bedrock Claude Integration [docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html]

### 4.5 Product Deduplication Service

**Purpose:** Remove duplicate products detected across multiple frames

**Implementation:**
```python
def deduplicate_products(all_products):
    """
    Deduplicate products based on brand + product_name + net_weight
    """
    seen = set()
    unique = []
    
    for product in all_products:
        key = f"{product.get('brand', '')}_{product.get('product_name', '')}_{product.get('net_weight', '')}"
        key = key.lower().strip()
        
        if key not in seen:
            seen.add(key)
            unique.append(product)
    
    return unique
```

### 4.6 Embedding Generation Service

**Purpose:** Generate vector embeddings for product similarity matching

**Titan Multimodal Embeddings:**
```python
def generate_embedding(image_bytes, text_description=None):
    """
    Generate 1024-dimensional embedding using Titan Multimodal Embeddings.
    Reference: docs.aws.amazon.com/bedrock/latest/userguide/titan-multiemb-models.html
    """
    bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
    
    body = {
        "inputImage": base64.b64encode(image_bytes).decode('utf-8'),
        "embeddingConfig": {
            "outputEmbeddingLength": 1024
        }
    }
    
    if text_description:
        body["inputText"] = text_description
    
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-image-v1',
        body=json.dumps(body)
    )
    
    result = json.loads(response['body'].read())
    return result['embedding']
```

### 4.7 Similarity Search Service

**Purpose:** Find existing products in database using vector similarity

**OpenSearch Serverless Query:**
```python
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def search_similar_products(embedding, threshold=0.92):
    """
    Search for similar products using k-NN.
    Reference: docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html
    """
    region = 'ap-south-1'
    service = 'aoss'
    credentials = boto3.Session().get_credentials()
    
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )
    
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    query = {
        "size": 1,
        "query": {
            "knn": {
                "product_embedding": {
                    "vector": embedding,
                    "k": 1
                }
            }
        }
    }
    
    response = client.search(index='products', body=query)
    
    if response['hits']['hits']:
        hit = response['hits']['hits'][0]
        score = hit['_score']
        if score >= threshold:
            return {
                'matched': True,
                'product_id': hit['_id'],
                'studio_image_url': hit['_source']['studio_image_url'],
                'similarity_score': score
            }
    
    return {'matched': False}
```

**OpenSearch Index Mapping:**
```json
{
  "mappings": {
    "properties": {
      "product_id": {"type": "keyword"},
      "brand": {"type": "text"},
      "product_name": {"type": "text"},
      "net_weight": {"type": "keyword"},
      "product_embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "faiss",
          "parameters": {
            "ef_construction": 128,
            "m": 24
          }
        }
      },
      "studio_image_url": {"type": "keyword"},
      "created_at": {"type": "date"}
    }
  }
}
```

### 4.8 Studio Image Generation Service

**Purpose:** Generate professional studio-quality product images

**Titan Image Generator v2:**
```python
def generate_studio_image(product_crop_bytes):
    """
    Generate studio image with white background.
    Reference: docs.aws.amazon.com/bedrock/latest/userguide/titan-image-models.html
    """
    bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
    
    body = json.dumps({
        "taskType": "OUTPAINTING",
        "outPaintingParams": {
            "image": base64.b64encode(product_crop_bytes).decode('utf-8'),
            "text": "Product on clean white studio background with soft professional lighting, e-commerce product photography style",
            "maskPrompt": "background",
            "outPaintingMode": "PRECISE"
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "width": 512,
            "height": 512,
            "cfgScale": 8.0
        }
    })
    
    response = bedrock.invoke_model(
        modelId='amazon.titan-image-generator-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    image_base64 = result['images'][0]
    return base64.b64decode(image_base64)
```

Reference: Titan Image Generator v2 [docs.aws.amazon.com/bedrock/latest/userguide/titan-image-models.html]

### 4.9 ONDC Formatting Service

**Purpose:** Format catalog to ONDC/Beckn protocol specification

**ONDC Item Schema:**
```python
def format_ondc_item(product, studio_image_url, store_id):
    """
    Format product to ONDC Retail Protocol schema.
    Reference: github.com/ONDC-Official/ONDC-Protocol-Specs
    """
    return {
        "id": str(uuid.uuid4()),
        "descriptor": {
            "name": f"{product['brand']} {product['product_name']}",
            "short_desc": product.get('variant', ''),
            "long_desc": f"{product['brand']} {product['product_name']} - {product['net_weight']}",
            "images": [
                {
                    "url": studio_image_url,
                    "size_type": "lg"
                }
            ]
        },
        "quantity": {
            "available": {
                "count": 0  # To be filled by shopkeeper
            },
            "maximum": {
                "count": 100
            }
        },
        "price": {
            "currency": "INR",
            "value": "0",  # To be filled by shopkeeper
            "maximum_value": "0"
        },
        "category_id": "grocery",  # Can be enhanced with classification
        "location_id": store_id,
        "fulfillment_id": "default",
        "@ondc/org/returnable": True,
        "@ondc/org/seller_pickup_return": True,
        "@ondc/org/time_to_ship": "P1D",
        "@ondc/org/available_on_cod": True
    }
```

---

## 5. Data Flow

### 5.1 Complete Data Flow Diagram

```
USER                           AWS CLOUD
 |
 |  1. Open App
 |----------------------------> Amplify (Frontend)
 |
 |  2. Login
 |----------------------------> Cognito (Auth)
 |<---------------------------- JWT Token
 |
 |  3. Request Upload URL
 |----------------------------> API Gateway
 |                              Lambda (GetPresignedURL)
 |<---------------------------- Presigned S3 URL
 |
 |  4. Upload Video
 |----------------------------> S3 (videos bucket)
 |                              |
 |                              v S3 Event
 |                              Step Functions
 |                              |
 |                              v
 |                              MediaConvert
 |                              (Extract 10-30 frames)
 |                              |
 |                              v
 |                              Lambda: FilterFrames
 |                              (Blur + SSIM filter)
 |                              Output: 3-5 frames
 |                              |
 |                              v
 |                              Bedrock: Claude 3.5 Haiku
 |                              (Product detection x 5)
 |                              Output: Product JSON
 |                              |
 |                              v
 |                              Lambda: Deduplicate
 |                              Output: Unique products
 |                              |
 |                              v
 |                              Bedrock: Titan Embed
 |                              (Generate embeddings)
 |                              |
 |                              v
 |                              OpenSearch Serverless
 |                              (k-NN similarity search)
 |                              |
 |                     +--------+--------+
 |                     |                 |
 |                  MATCH             NO MATCH
 |                     |                 |
 |                     v                 v
 |               Reuse existing    Bedrock: Titan Image
 |               studio image      (Generate new image)
 |                     |                 |
 |                     +--------+--------+
 |                              |
 |                              v
 |                              Lambda: FormatONDC
 |                              (Beckn JSON schema)
 |                              |
 |                              v
 |                              DynamoDB
 |                              (Store catalog)
 |
 |  5. Poll Status
 |----------------------------> API Gateway
 |                              Lambda (GetJobStatus)
 |                              DynamoDB (Jobs table)
 |<---------------------------- Status: COMPLETED
 |
 |  6. Get Catalog
 |----------------------------> API Gateway
 |                              Lambda (GetCatalog)
 |                              DynamoDB (Catalog table)
 |<---------------------------- ONDC JSON Catalog
 |
 |  7. Review & Edit
 |  (Add prices, corrections)
 |
 |  8. Confirm Catalog
 |----------------------------> API Gateway
 |                              Lambda (UpdateCatalog)
 |                              DynamoDB
 |<---------------------------- Success
```

### 5.2 State Transitions

| State | Trigger | Next State | Data |
|-------|---------|------------|------|
| UPLOADED | S3 event | EXTRACTING | video_key |
| EXTRACTING | MediaConvert complete | FILTERING | frame_keys[] |
| FILTERING | Lambda complete | DETECTING | quality_frames[] |
| DETECTING | Bedrock complete | DEDUPLICATING | products[] |
| DEDUPLICATING | Lambda complete | EMBEDDING | unique_products[] |
| EMBEDDING | Bedrock complete | SEARCHING | embeddings[] |
| SEARCHING | OpenSearch complete | GENERATING | new_products[], matched_products[] |
| GENERATING | Bedrock complete | FORMATTING | all_products_with_images[] |
| FORMATTING | Lambda complete | COMPLETED | ondc_catalog |

---

## 6. Database Design

### 6.1 DynamoDB Tables

**Table: Jobs**
```
Primary Key: job_id (String)
Sort Key: None

Attributes:
- job_id: String (UUID)
- user_id: String (Cognito sub)
- store_id: String
- video_key: String (S3 key)
- status: String (UPLOADED|EXTRACTING|FILTERING|DETECTING|...)
- created_at: String (ISO 8601)
- updated_at: String (ISO 8601)
- frame_count: Number
- product_count: Number
- error_message: String (if failed)

GSI: user_id-created_at-index
  - Partition Key: user_id
  - Sort Key: created_at
```

**Table: Catalogs**
```
Primary Key: store_id (String)
Sort Key: catalog_id (String)

Attributes:
- store_id: String
- catalog_id: String (UUID)
- job_id: String
- status: String (DRAFT|PUBLISHED)
- ondc_catalog: Map (Full ONDC JSON)
- product_count: Number
- created_at: String (ISO 8601)
- published_at: String (ISO 8601)
```

**Table: Products (for hybrid cataloging cache)**
```
Primary Key: product_hash (String)
Sort Key: None

Attributes:
- product_hash: String (MD5 of brand+name+weight)
- brand: String
- product_name: String
- net_weight: String
- variant: String
- embedding: List<Number> (1024 dims)
- studio_image_url: String
- usage_count: Number
- created_at: String
- last_used_at: String
```

### 6.2 OpenSearch Serverless Index

**Collection:** kiranastudio-products
**Type:** VECTORSEARCH

**Index Mapping:** See Section 4.7

---

## 7. API Design

### 7.1 REST API Endpoints

**Base URL:** `https://api.kiranastudio.in/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /upload/presigned-url | Get presigned URL for video upload |
| POST | /jobs | Create new processing job |
| GET | /jobs/{job_id} | Get job status |
| GET | /jobs/{job_id}/catalog | Get generated catalog |
| PUT | /catalogs/{catalog_id} | Update catalog (add prices) |
| POST | /catalogs/{catalog_id}/publish | Publish to ONDC |

### 7.2 API Request/Response Examples

**POST /upload/presigned-url**
```json
// Request
{
  "content_type": "video/mp4",
  "file_size": 15000000
}

// Response
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "upload_url": "https://kiranastudio-videos.s3.ap-south-1.amazonaws.com/...",
  "expires_in": 300
}
```

**GET /jobs/{job_id}**
```json
// Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "product_count": 24,
  "processing_time_ms": 45000,
  "catalog_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**GET /jobs/{job_id}/catalog**
```json
// Response (ONDC Beckn format)
{
  "context": {
    "domain": "nic2004:52110",
    "action": "on_search",
    "country": "IND"
  },
  "message": {
    "catalog": {
      "bpp/descriptor": {
        "name": "Store Name"
      },
      "bpp/providers": [
        {
          "id": "store_123",
          "items": [
            {
              "id": "item_1",
              "descriptor": {
                "name": "Parle-G 100g",
                "images": [{"url": "https://..."}]
              },
              "price": {
                "currency": "INR",
                "value": "10"
              }
            }
          ]
        }
      ]
    }
  }
}
```

---

## 8. Algorithm Details

### 8.1 Blur Detection Algorithm

**Method:** Laplacian Variance

**Theory:**
The Laplacian operator computes the second derivative of an image, highlighting regions of rapid intensity change (edges). Sharp images have well-defined edges resulting in high Laplacian variance. Blurry images have gradual transitions resulting in low variance.

**Formula:**
```
Blur Score = Var(Laplacian(grayscale_image))
```

**Implementation:**
```python
def laplacian_variance(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return variance
```

**Threshold Selection:**
- < 100: Very blurry (reject)
- 100-500: Acceptable
- > 500: Sharp

Reference: PyImageSearch [pyimagesearch.com/2015/09/07/blur-detection-with-opencv]

### 8.2 Frame Deduplication Algorithm

**Method:** Structural Similarity Index (SSIM)

**Theory:**
SSIM measures the perceptual similarity between two images based on luminance, contrast, and structure. Value ranges from -1 to 1, where 1 indicates identical images.

**Formula:**
```
SSIM(x,y) = [l(x,y)]^a * [c(x,y)]^b * [s(x,y)]^c

Where:
- l(x,y) = luminance comparison
- c(x,y) = contrast comparison
- s(x,y) = structure comparison
```

**Implementation:**
```python
from skimage.metrics import structural_similarity as ssim

def is_duplicate(img1, img2, threshold=0.95):
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score = ssim(gray1, gray2)
    return score > threshold
```

Reference: scikit-image [scikit-image.org/docs/stable/api/skimage.metrics.html]

### 8.3 Vector Similarity Search

**Method:** k-Nearest Neighbors with HNSW

**Theory:**
Hierarchical Navigable Small World (HNSW) is a graph-based approximate nearest neighbor algorithm. It builds a multi-layer graph where each layer is a navigable small world graph.

**Distance Metric:** Cosine Similarity
```
cosine_similarity(A, B) = (A . B) / (||A|| * ||B||)
```

**Index Parameters:**
- ef_construction: 128 (affects index build quality)
- m: 24 (number of bi-directional links per node)

Reference: OpenSearch k-NN [docs.aws.amazon.com/opensearch-service/latest/developerguide/knn.html]

---

## 9. Security Design

### 9.1 Authentication Flow

```
+--------+     +----------+     +---------+     +-------------+
| Mobile |---->| Cognito  |---->| API GW  |---->| Lambda      |
| App    |     | (Auth)   |     | (JWT)   |     | (Business)  |
+--------+     +----------+     +---------+     +-------------+
     |              |                |
     |  1. Login    |                |
     |------------->|                |
     |              |                |
     |  2. JWT      |                |
     |<-------------|                |
     |              |                |
     |  3. API Call (Bearer token)   |
     |------------------------------>|
     |              |                |
     |  4. Validate |                |
     |              |<---------------|
     |              |                |
     |  5. Claims   |                |
     |              |--------------->|
```

### 9.2 Security Controls

| Layer | Control | Implementation |
|-------|---------|----------------|
| Transport | TLS 1.2+ | API Gateway default |
| Authentication | JWT | Cognito User Pools |
| Authorization | IAM + RBAC | Lambda execution roles |
| Data at Rest | Encryption | S3 SSE-S3, DynamoDB encryption |
| Data in Transit | HTTPS | All API calls |
| API Protection | Throttling | API Gateway usage plans |
| Secrets | Secrets Manager | API keys, credentials |
| Logging | Audit Trail | CloudTrail enabled |

### 9.3 IAM Roles

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::kiranastudio-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-5-haiku*",
        "arn:aws:bedrock:ap-south-1::foundation-model/amazon.titan-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:*:table/kiranastudio-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "arn:aws:aoss:ap-south-1:*:collection/*"
    }
  ]
}
```

---

## 10. Scalability Considerations

### 10.1 Current Design Capacity

| Component | Limit | Scaling Method |
|-----------|-------|----------------|
| S3 | Unlimited | Automatic |
| Lambda | 1000 concurrent | Request increase |
| Step Functions | 25000 executions/sec | Standard workflows |
| Bedrock | Model-specific | Provisioned throughput |
| OpenSearch Serverless | Auto-scaling OCUs | Configuration |
| DynamoDB | Unlimited (on-demand) | Automatic |

### 10.2 Bottlenecks and Mitigations

| Bottleneck | Mitigation |
|------------|------------|
| Bedrock rate limits | Implement retry with exponential backoff |
| Lambda cold starts | Use provisioned concurrency for critical paths |
| OpenSearch query latency | Tune HNSW parameters, use caching |
| Large video uploads | Client-side compression, chunked upload |

### 10.3 Multi-Region Strategy (Future)

```
                    Route 53
                       |
           +-----------+-----------+
           |                       |
     ap-south-1              ap-southeast-1
     (Mumbai)                (Singapore)
           |                       |
    +------+------+         +------+------+
    | Full Stack  |         | Full Stack  |
    +-------------+         +-------------+
           |                       |
           +-------DynamoDB--------+
                 Global Tables
```

---

## 11. Error Handling

### 11.1 Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| Client Errors | Invalid video format, too large | Return 4xx, user message |
| Processing Errors | Blur detection fail, no products found | Retry, then fail gracefully |
| AI Errors | Bedrock timeout, invalid response | Retry with backoff |
| Infrastructure | S3 unavailable, Lambda timeout | Circuit breaker, fallback |

### 11.2 Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def invoke_bedrock_with_retry(model_id, body):
    return bedrock.invoke_model(modelId=model_id, body=body)
```

### 11.3 Fallback Mechanisms

| Failure | Fallback |
|---------|----------|
| Studio image generation fails | Use cropped original image |
| Product detection returns empty | Flag for manual entry |
| Similarity search unavailable | Generate all images (no reuse) |
| ONDC formatting fails | Return raw JSON for manual formatting |

---

## 12. References

### AWS Documentation
- Step Functions: docs.aws.amazon.com/step-functions/latest/dg/welcome.html
- Bedrock: docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
- MediaConvert: docs.aws.amazon.com/mediaconvert/latest/ug/what-is.html
- OpenSearch Serverless: docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html
- DynamoDB: docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html

### Algorithm References
- Blur Detection: pyimagesearch.com/2015/09/07/blur-detection-with-opencv
- SSIM: scikit-image.org/docs/stable/api/skimage.metrics.html
- HNSW: arxiv.org/abs/1603.09320

### Protocol References
- ONDC Protocol: github.com/ONDC-Official/ONDC-Protocol-Specs
- Beckn Protocol: developers.becknprotocol.io/docs/introduction/beckn-protocol-specification

### AWS Sample Repositories
- Titan Multimodal Search: github.com/aws-samples/amazon-bedrock-titan-multimodal-search
- Step Functions + Bedrock: github.com/aws-samples/step-functions-workflows-collection

---

**Document Version:** 1.0  
**Author:** Team MotherBoard  
**Last Updated:** February 2026
