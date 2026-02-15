# KiranaStudio - Requirements Document

**Project:** KiranaStudio - Video-Based Catalog Generation Pipeline  
**Team:** MotherBoard  
**Version:** 1.0  
**Last Updated:** February 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Stakeholders](#2-stakeholders)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Technical Requirements](#5-technical-requirements)
6. [Integration Requirements](#6-integration-requirements)
7. [Data Requirements](#7-data-requirements)
8. [User Interface Requirements](#8-user-interface-requirements)
9. [Constraints](#9-constraints)
10. [Assumptions](#10-assumptions)
11. [Dependencies](#11-dependencies)
12. [Acceptance Criteria](#12-acceptance-criteria)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for KiranaStudio, a GenAI-powered system that transforms video recordings of retail shelves into ONDC-compliant digital catalogs with studio-quality product images.

### 1.2 Scope

KiranaStudio covers the following capabilities:
- Video capture and upload from mobile devices
- Automated frame extraction and quality filtering
- AI-powered product detection and information extraction
- Studio-quality image generation using generative AI
- ONDC/Beckn protocol compliant catalog output
- Product similarity matching for cost optimization

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| ONDC | Open Network for Digital Commerce |
| VLM | Vision-Language Model |
| k-NN | k-Nearest Neighbors algorithm |
| SSIM | Structural Similarity Index Measure |
| SKU | Stock Keeping Unit |
| GenAI | Generative Artificial Intelligence |
| OCR | Optical Character Recognition |
| HNSW | Hierarchical Navigable Small World |

---

## 2. Stakeholders

### 2.1 Primary Users

| Stakeholder | Description | Needs |
|-------------|-------------|-------|
| Kirana Shopkeeper | Small retail store owner with limited tech literacy | Simple video-based catalog creation, minimal typing |
| Store Manager | Manages multiple stores or larger retail | Batch processing, catalog management |

### 2.2 Secondary Users

| Stakeholder | Description | Needs |
|-------------|-------------|-------|
| ONDC Network | Digital commerce infrastructure | Compliant catalog format |
| System Administrator | Manages KiranaStudio platform | Monitoring, troubleshooting |

---

## 3. Functional Requirements

### 3.1 Video Capture Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-VC-001 | System shall provide a camera interface for video recording | Must Have |
| FR-VC-002 | System shall enforce landscape orientation for video capture | Must Have |
| FR-VC-003 | System shall display a stabilization guide overlay during recording | Should Have |
| FR-VC-004 | System shall limit video duration to 10-60 seconds | Must Have |
| FR-VC-005 | System shall support video resolution up to 1080p | Must Have |
| FR-VC-006 | System shall support MP4 video format | Must Have |
| FR-VC-007 | System shall provide real-time recording duration indicator | Should Have |
| FR-VC-008 | System shall allow video preview before upload | Should Have |
| FR-VC-009 | System shall allow re-recording if user is not satisfied | Must Have |

### 3.2 Video Upload Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-VU-001 | System shall generate secure presigned URLs for video upload | Must Have |
| FR-VU-002 | System shall upload video directly to cloud storage | Must Have |
| FR-VU-003 | System shall display upload progress to user | Must Have |
| FR-VU-004 | System shall handle upload interruptions with retry capability | Should Have |
| FR-VU-005 | System shall validate video file before upload (format, size) | Must Have |
| FR-VU-006 | System shall limit maximum video file size to 100MB | Must Have |
| FR-VU-007 | System shall compress video on device if exceeding size limit | Could Have |

### 3.3 Frame Extraction Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-FE-001 | System shall extract frames from uploaded video at configurable rate | Must Have |
| FR-FE-002 | System shall extract minimum 1 frame per second | Must Have |
| FR-FE-003 | System shall output frames in JPEG format | Must Have |
| FR-FE-004 | System shall preserve frame quality at minimum 80% JPEG quality | Must Have |
| FR-FE-005 | System shall store extracted frames in cloud storage | Must Have |

### 3.4 Frame Quality Filter Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-FF-001 | System shall detect and reject blurry frames using Laplacian variance | Must Have |
| FR-FF-002 | System shall use configurable blur threshold (default: 100) | Should Have |
| FR-FF-003 | System shall detect and remove duplicate frames using SSIM | Must Have |
| FR-FF-004 | System shall use configurable similarity threshold (default: 0.95) | Should Have |
| FR-FF-005 | System shall select top 3-5 quality frames for processing | Must Have |
| FR-FF-006 | System shall prioritize frames with highest sharpness scores | Must Have |

### 3.5 Product Detection Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PD-001 | System shall detect all visible products in shelf images | Must Have |
| FR-PD-002 | System shall extract brand name from product labels | Must Have |
| FR-PD-003 | System shall extract product name from product labels | Must Have |
| FR-PD-004 | System shall extract net weight/volume from product labels | Must Have |
| FR-PD-005 | System shall extract variant type when visible | Should Have |
| FR-PD-006 | System shall ignore partially visible or cut-off products | Must Have |
| FR-PD-007 | System shall output product data in structured JSON format | Must Have |
| FR-PD-008 | System shall process multiple frames in parallel | Should Have |
| FR-PD-009 | System shall handle products with non-English text | Could Have |

### 3.6 Product Deduplication Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-DD-001 | System shall identify duplicate products across frames | Must Have |
| FR-DD-002 | System shall merge duplicate products into single entry | Must Have |
| FR-DD-003 | System shall use brand+name+weight as deduplication key | Must Have |
| FR-DD-004 | System shall handle case-insensitive matching | Must Have |

### 3.7 Embedding Generation Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-EG-001 | System shall generate vector embeddings for product images | Must Have |
| FR-EG-002 | System shall use 1024-dimensional embeddings | Must Have |
| FR-EG-003 | System shall support multimodal embeddings (image + text) | Should Have |
| FR-EG-004 | System shall process embeddings in parallel for efficiency | Should Have |

### 3.8 Similarity Search Module (Hybrid Cataloging)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-SS-001 | System shall search existing product database for matches | Must Have |
| FR-SS-002 | System shall use k-NN algorithm for similarity search | Must Have |
| FR-SS-003 | System shall use configurable similarity threshold (default: 0.92) | Should Have |
| FR-SS-004 | System shall return existing studio image URL for matched products | Must Have |
| FR-SS-005 | System shall flag unmatched products for image generation | Must Have |
| FR-SS-006 | System shall index new products for future matching | Must Have |

### 3.9 Studio Image Generation Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-IG-001 | System shall generate studio-quality images for new products | Must Have |
| FR-IG-002 | System shall remove original background from product crops | Must Have |
| FR-IG-003 | System shall generate clean white studio background | Must Have |
| FR-IG-004 | System shall apply professional lighting effect | Should Have |
| FR-IG-005 | System shall output images in consistent dimensions (512x512) | Must Have |
| FR-IG-006 | System shall store generated images in cloud storage | Must Have |
| FR-IG-007 | System shall fallback to cropped original if generation fails | Must Have |

### 3.10 ONDC Catalog Formatting Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CF-001 | System shall format catalog to ONDC Retail Protocol schema | Must Have |
| FR-CF-002 | System shall include descriptor fields (name, images) | Must Have |
| FR-CF-003 | System shall include price fields (with placeholder values) | Must Have |
| FR-CF-004 | System shall include quantity fields | Must Have |
| FR-CF-005 | System shall include category_id field | Should Have |
| FR-CF-006 | System shall include ONDC-specific attributes | Should Have |
| FR-CF-007 | System shall validate JSON against Beckn schema | Should Have |

### 3.11 Catalog Review and Edit Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RE-001 | System shall display detected products in grid view | Must Have |
| FR-RE-002 | System shall allow editing of any product field | Must Have |
| FR-RE-003 | System shall require price entry for all products | Must Have |
| FR-RE-004 | System shall allow deletion of incorrect products | Must Have |
| FR-RE-005 | System shall allow manual addition of missed products | Could Have |
| FR-RE-006 | System shall show confidence score for AI detection | Should Have |
| FR-RE-007 | System shall highlight low-confidence detections | Should Have |

### 3.12 Catalog Publishing Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CP-001 | System shall save draft catalogs | Must Have |
| FR-CP-002 | System shall allow catalog export as JSON file | Must Have |
| FR-CP-003 | System shall track catalog status (Draft/Published) | Must Have |
| FR-CP-004 | System shall integrate with ONDC seller applications | Could Have |

### 3.13 User Management Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-UM-001 | System shall support user registration | Must Have |
| FR-UM-002 | System shall support user login with email/password | Must Have |
| FR-UM-003 | System shall support phone number authentication | Should Have |
| FR-UM-004 | System shall maintain user session | Must Have |
| FR-UM-005 | System shall support password reset | Should Have |
| FR-UM-006 | System shall associate catalogs with user accounts | Must Have |

### 3.14 Job Management Module

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-JM-001 | System shall track processing job status | Must Have |
| FR-JM-002 | System shall provide job status API | Must Have |
| FR-JM-003 | System shall notify user on job completion | Should Have |
| FR-JM-004 | System shall maintain job history | Should Have |
| FR-JM-005 | System shall allow job cancellation | Could Have |

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P-001 | Video upload time | < 30 seconds for 50MB video on 4G |
| NFR-P-002 | End-to-end processing time | < 2 minutes for 10-second video |
| NFR-P-003 | Frame extraction latency | < 10 seconds for 30 frames |
| NFR-P-004 | Product detection latency per frame | < 5 seconds |
| NFR-P-005 | Similarity search latency | < 500ms per query |
| NFR-P-006 | Image generation latency | < 10 seconds per image |
| NFR-P-007 | API response time | < 500ms for 95th percentile |
| NFR-P-008 | App startup time | < 3 seconds |

### 4.2 Scalability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-S-001 | Concurrent video uploads | 10,000+ |
| NFR-S-002 | Daily processing capacity | 100,000+ catalogs |
| NFR-S-003 | Product database size | 1,000,000+ products |
| NFR-S-004 | Vector index size | 10,000,000+ embeddings |
| NFR-S-005 | Storage capacity | Unlimited (cloud storage) |

### 4.3 Availability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-A-001 | System uptime | 99.9% (excluding planned maintenance) |
| NFR-A-002 | Planned maintenance window | < 4 hours per month |
| NFR-A-003 | Recovery Time Objective (RTO) | < 1 hour |
| NFR-A-004 | Recovery Point Objective (RPO) | < 15 minutes |

### 4.4 Reliability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-R-001 | Product detection accuracy | > 85% for standard FMCG products |
| NFR-R-002 | OCR accuracy for English labels | > 90% |
| NFR-R-003 | Similarity match precision | > 95% |
| NFR-R-004 | Processing success rate | > 98% |
| NFR-R-005 | Data durability | 99.999999999% (11 nines) |

### 4.5 Security Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-SEC-001 | All data in transit must use TLS 1.2+ | Must Have |
| NFR-SEC-002 | All data at rest must be encrypted | Must Have |
| NFR-SEC-003 | User authentication required for all operations | Must Have |
| NFR-SEC-004 | API rate limiting to prevent abuse | Must Have |
| NFR-SEC-005 | Audit logging for all user actions | Should Have |
| NFR-SEC-006 | Secrets must be stored in secure vault | Must Have |
| NFR-SEC-007 | No PII in application logs | Must Have |

### 4.6 Compliance Requirements

| ID | Requirement | Standard |
|----|-------------|----------|
| NFR-C-001 | ONDC Retail Protocol compliance | ONDC v2.0 |
| NFR-C-002 | Data residency in India | AWS ap-south-1 |
| NFR-C-003 | Cloud security compliance | SOC 2, ISO 27001 |

### 4.7 Usability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-U-001 | Time to complete first catalog | < 5 minutes |
| NFR-U-002 | User actions to complete catalog | < 10 taps |
| NFR-U-003 | Error message clarity | Non-technical, actionable |
| NFR-U-004 | Supported languages (UI) | English, Hindi |
| NFR-U-005 | Accessibility compliance | WCAG 2.1 Level A |

### 4.8 Maintainability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-M-001 | Code test coverage | > 80% |
| NFR-M-002 | Deployment frequency | Multiple per day |
| NFR-M-003 | Mean time to deploy | < 15 minutes |
| NFR-M-004 | Rollback capability | < 5 minutes |

---

## 5. Technical Requirements

### 5.1 Cloud Infrastructure (AWS)

| Component | AWS Service | Justification |
|-----------|-------------|---------------|
| Compute | AWS Lambda | Serverless, pay-per-use, auto-scaling |
| Orchestration | AWS Step Functions | Visual workflow, parallel processing, error handling |
| Video Processing | AWS MediaConvert | Managed transcoding, frame extraction |
| Object Storage | Amazon S3 | Unlimited scale, durability, cost-effective |
| Database | Amazon DynamoDB | Serverless NoSQL, single-digit ms latency |
| Vector Search | Amazon OpenSearch Serverless | Managed k-NN, auto-scaling |
| GenAI | Amazon Bedrock | Managed foundation models, no GPU management |
| API | Amazon API Gateway | Managed REST APIs, throttling, caching |
| Authentication | Amazon Cognito | Managed user pools, JWT tokens |
| Frontend Hosting | AWS Amplify | CI/CD, CDN, custom domains |
| Monitoring | Amazon CloudWatch | Logs, metrics, alarms, dashboards |
| Secrets | AWS Secrets Manager | Secure credential storage |

### 5.2 GenAI Models (Amazon Bedrock)

| Model | Model ID | Purpose |
|-------|----------|---------|
| Claude 3.5 Haiku | anthropic.claude-3-5-haiku-20241022-v1:0 | Product detection, OCR |
| Titan Multimodal Embeddings | amazon.titan-embed-image-v1 | Vector embeddings |
| Titan Image Generator v2 | amazon.titan-image-generator-v2:0 | Studio image generation |

Reference: Amazon Bedrock Model IDs [docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html]

### 5.3 Programming Languages and Frameworks

| Component | Technology | Version |
|-----------|------------|---------|
| Backend (Lambda) | Python | 3.11+ |
| Image Processing | OpenCV | 4.8+ |
| SSIM Calculation | scikit-image | 0.21+ |
| AWS SDK | Boto3 | Latest |
| Mobile App | React Native | 0.73+ |
| Web App | React | 18.x |
| State Management | Redux Toolkit | Latest |
| HTTP Client | Axios | Latest |

### 5.4 Development Tools

| Tool | Purpose |
|------|---------|
| AWS SAM | Infrastructure as Code, local testing |
| AWS CDK | Infrastructure as Code (alternative) |
| GitHub | Source control |
| GitHub Actions | CI/CD pipeline |
| Jest | JavaScript testing |
| Pytest | Python testing |
| ESLint | JavaScript linting |
| Black | Python formatting |

---

## 6. Integration Requirements

### 6.1 ONDC Integration

| ID | Requirement | Description |
|----|-------------|-------------|
| IR-ONDC-001 | Output format must comply with Beckn Protocol | JSON schema validation |
| IR-ONDC-002 | Support on_search callback format | Catalog response structure |
| IR-ONDC-003 | Include mandatory ONDC fields | descriptor, price, quantity, category_id |
| IR-ONDC-004 | Support ONDC item taxonomy | Category mapping |

Reference: ONDC Protocol Specs [github.com/ONDC-Official/ONDC-Protocol-Specs]

### 6.2 AWS Service Integration

| ID | Requirement | Integration Pattern |
|----|-------------|---------------------|
| IR-AWS-001 | S3 event triggers Step Functions | EventBridge rule |
| IR-AWS-002 | Step Functions invokes Bedrock | Direct service integration |
| IR-AWS-003 | Lambda accesses OpenSearch | VPC endpoint or public endpoint |
| IR-AWS-004 | API Gateway authenticates via Cognito | Authorizer |
| IR-AWS-005 | CloudWatch receives all logs | AWS SDK automatic |

### 6.3 Third-Party Integration (Future)

| ID | Integration | Purpose | Priority |
|----|-------------|---------|----------|
| IR-TP-001 | ONDC Seller Apps | Direct catalog publishing | Could Have |
| IR-TP-002 | Payment Gateways | Subscription billing | Could Have |
| IR-TP-003 | Analytics Platforms | Usage analytics | Could Have |

---

## 7. Data Requirements

### 7.1 Input Data

| Data Type | Format | Size Limit | Validation |
|-----------|--------|------------|------------|
| Video | MP4 (H.264) | 100MB | Format, duration 10-60s |
| Video Resolution | 720p-1080p | - | Aspect ratio 16:9 |

### 7.2 Output Data

| Data Type | Format | Description |
|-----------|--------|-------------|
| Catalog | JSON (Beckn) | ONDC-compliant catalog |
| Studio Images | JPEG | 512x512, white background |
| Embeddings | Float array | 1024 dimensions |

### 7.3 Data Retention

| Data Type | Retention Period | Storage Class |
|-----------|------------------|---------------|
| Raw Videos | 7 days | S3 Standard |
| Extracted Frames | 24 hours | S3 Standard |
| Studio Images | Indefinite | S3 Standard-IA |
| Catalogs | Indefinite | DynamoDB |
| Embeddings | Indefinite | OpenSearch |
| Job Logs | 30 days | CloudWatch |

### 7.4 Data Privacy

| Requirement | Implementation |
|-------------|----------------|
| No PII collection beyond necessary | Only store email, phone |
| Data residency | ap-south-1 (Mumbai) only |
| User data deletion | Support account deletion |
| Data encryption | At rest and in transit |

---

## 8. User Interface Requirements

### 8.1 Mobile App Requirements

| ID | Requirement | Platform |
|----|-------------|----------|
| UI-M-001 | Support Android 8.0+ | Android |
| UI-M-002 | Support iOS 14.0+ | iOS |
| UI-M-003 | Responsive layout for phones and tablets | Both |
| UI-M-004 | Camera access permission handling | Both |
| UI-M-005 | Offline indicator when no connectivity | Both |

### 8.2 Screen Requirements

| Screen | Key Elements |
|--------|--------------|
| Home | Camera button, recent scans list |
| Camera | Viewfinder, stabilization guide, record button |
| Upload | Progress bar, cancel button |
| Processing | Status indicator, estimated time |
| Review | Product grid, edit button per product |
| Edit Product | Form fields, save/delete buttons |
| Catalog View | Complete catalog, export button |

### 8.3 Accessibility Requirements

| ID | Requirement | Standard |
|----|-------------|----------|
| UI-A-001 | Color contrast ratio minimum 4.5:1 | WCAG 2.1 |
| UI-A-002 | Touch targets minimum 44x44 pixels | iOS HIG |
| UI-A-003 | Screen reader compatibility | VoiceOver, TalkBack |
| UI-A-004 | Text scaling support up to 200% | WCAG 2.1 |

---

## 9. Constraints

### 9.1 Technical Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| AWS Only | Must use AWS services exclusively | No multi-cloud |
| Bedrock Model Availability | Models available in ap-south-1 only | Region locked |
| Video Length | 10-60 seconds maximum | UX limitation |
| Frame Rate | 1 frame/second extraction | Processing speed |
| Embedding Dimensions | 1024 fixed for Titan | Index compatibility |

### 9.2 Business Constraints

| Constraint | Description |
|------------|-------------|
| Budget | Optimize for cost efficiency |
| Timeline | MVP within hackathon duration |
| Team Size | 3 members |

### 9.3 Regulatory Constraints

| Constraint | Description |
|------------|-------------|
| Data Residency | All data must remain in India |
| ONDC Compliance | Must follow ONDC protocol specifications |

---

## 10. Assumptions

| ID | Assumption | Risk if False |
|----|------------|---------------|
| A-001 | Users have smartphones with cameras | Cannot capture video |
| A-002 | Users have internet connectivity for upload | Cannot process catalog |
| A-003 | Product labels are in English | Lower OCR accuracy |
| A-004 | Products are standard FMCG items | Lower detection accuracy |
| A-005 | Shelves have adequate lighting | Blurry frame rejection |
| A-006 | AWS Bedrock models remain available | Service dependency |
| A-007 | ONDC protocol schema remains stable | Format changes needed |

---

## 11. Dependencies

### 11.1 External Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| AWS Services | Cloud Infrastructure | Critical |
| Amazon Bedrock | GenAI Models | Critical |
| Claude 3.5 Haiku | Vision-Language Model | Critical |
| Titan Image Generator | Image Generation | Critical |
| Titan Embeddings | Vector Generation | Critical |
| OpenSearch Serverless | Vector Search | High |
| ONDC Protocol | Output Format | High |

### 11.2 Internal Dependencies

| Component | Depends On |
|-----------|------------|
| Frame Filter | Frame Extraction |
| Product Detection | Frame Filter |
| Embedding Generation | Product Detection |
| Similarity Search | Embedding Generation |
| Image Generation | Similarity Search |
| ONDC Formatting | Image Generation |

---

## 12. Acceptance Criteria

### 12.1 Functional Acceptance

| ID | Criteria | Verification |
|----|----------|--------------|
| AC-F-001 | User can record and upload video | Manual test |
| AC-F-002 | System extracts frames from video | Log verification |
| AC-F-003 | System filters blurry and duplicate frames | Output inspection |
| AC-F-004 | System detects products with > 85% accuracy | Test dataset |
| AC-F-005 | System generates studio images | Visual inspection |
| AC-F-006 | System outputs valid ONDC JSON | Schema validation |
| AC-F-007 | User can edit detected products | Manual test |
| AC-F-008 | User can export final catalog | Manual test |

### 12.2 Performance Acceptance

| ID | Criteria | Verification |
|----|----------|--------------|
| AC-P-001 | End-to-end processing < 2 minutes | Timer measurement |
| AC-P-002 | API response < 500ms (95th percentile) | CloudWatch metrics |
| AC-P-003 | System handles 100 concurrent users | Load test |

### 12.3 Security Acceptance

| ID | Criteria | Verification |
|----|----------|--------------|
| AC-S-001 | All APIs require authentication | Penetration test |
| AC-S-002 | All data encrypted at rest | AWS console verification |
| AC-S-003 | All traffic uses HTTPS | Certificate check |

---

## Appendix A: Reference Documents

| Document | Source |
|----------|--------|
| AWS Well-Architected Framework | docs.aws.amazon.com/wellarchitected |
| Amazon Bedrock User Guide | docs.aws.amazon.com/bedrock |
| ONDC Protocol Specifications | github.com/ONDC-Official/ONDC-Protocol-Specs |
| Beckn Protocol Documentation | developers.becknprotocol.io |
| OpenCV Documentation | docs.opencv.org |
| scikit-image Documentation | scikit-image.org/docs |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| Catalog | Collection of product listings for a store |
| Embedding | Dense vector representation of data |
| Frame | Single image extracted from video |
| Hybrid Cataloging | Reusing existing images vs generating new ones |
| k-NN | Algorithm finding closest vectors in space |
| Laplacian | Edge detection operator for blur measurement |
| ONDC | India's open e-commerce network |
| Presigned URL | Temporary secure URL for S3 upload |
| SSIM | Metric measuring image similarity |
| Studio Image | Professional product photo with clean background |
| VLM | AI model understanding both images and text |

---

## Appendix C: Traceability Matrix

| FR ID | Requirement | Design Section | Component |
|-------|-------------|----------------|-----------|
| FR-VC-001 to FR-VC-009 | Video Capture Module | UI Screens (Section 8.2) | Mobile App |
| FR-VU-001 to FR-VU-007 | Video Upload Module | 4.1 Video Upload Service | Lambda: GeneratePresignedURL |
| FR-FE-001 to FR-FE-005 | Frame Extraction Module | 4.2 Frame Extraction Service | MediaConvert |
| FR-FF-001 to FR-FF-006 | Frame Quality Filter Module | 4.3 Frame Filter Service, 8.1, 8.2 | Lambda: FilterFrames |
| FR-PD-001 to FR-PD-009 | Product Detection Module | 4.4 Product Detection Service | Claude 3.5 Haiku |
| FR-DD-001 to FR-DD-004 | Product Deduplication Module | 4.5 Product Deduplication Service | Lambda: DeduplicateProducts |
| FR-EG-001 to FR-EG-004 | Embedding Generation Module | 4.6 Embedding Generation Service | Titan Embeddings |
| FR-SS-001 to FR-SS-006 | Similarity Search Module | 4.7 Similarity Search Service | OpenSearch Serverless |
| FR-IG-001 to FR-IG-007 | Studio Image Generation Module | 4.8 Studio Image Generation Service | Titan Image Generator |
| FR-CF-001 to FR-CF-007 | ONDC Catalog Formatting Module | 4.9 ONDC Formatting Service | Lambda: FormatONDC |
| FR-RE-001 to FR-RE-007 | Catalog Review and Edit Module | UI Screens (Section 8.2) | Mobile/Web App |
| FR-CP-001 to FR-CP-004 | Catalog Publishing Module | 7.1 REST API Endpoints | Lambda: UpdateCatalog |
| FR-UM-001 to FR-UM-006 | User Management Module | 9.1 Authentication Flow | Cognito |
| FR-JM-001 to FR-JM-005 | Job Management Module | 5.2 State Transitions, 7.1 | DynamoDB, Step Functions |

---

**Document Version:** 1.1  
**Author:** Team MotherBoard  
**Last Updated:** February 2026
