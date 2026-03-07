export interface JobStatusResponse {
  job_id: string;
  video_id: string;
  status: string;
  product_count: number;
  error_message: string | null;
  catalog_id: string | null;
  updated_at: string;
}

export interface UseSampleResponse {
  video_id: string;
  job_id: string;
  message: string;
}

export interface ProcessJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface NutritionFacts {
  energy?: string | null;
  protein?: string | null;
  fat?: string | null;
  carbs?: string | null;
  sodium?: string | null;
  [key: string]: string | null | undefined;
}

export interface ProductImage {
  image_id: string;
  image_url: string;
  frame_type?: string | null;
}

export interface CatalogProduct {
  product_id: string;
  brand: string | null;
  product_name: string;
  variant: string | null;
  category: string | null;
  net_weight: string | null;
  price: number | null;
  image_url: string | null;

  // Rich fields from multi-frame extraction
  ingredients: string | null;
  nutrition_facts: NutritionFacts | null;
  barcode: string | null;
  fssai_license: string | null;
  manufacturer: string | null;
  shelf_life: string | null;
  description: string | null;
  tags: string[] | null;

  // Multiple angle images
  images: ProductImage[] | null;
}

export interface CatalogResponse {
  catalog_id: string;
  job_id: string;
  status: string;
  products: CatalogProduct[];
  ondc_catalog: Record<string, unknown>;
  created_at: string;
}

export interface UpdateCatalogResponse {
  status: string;
  catalog_id: string;
}

export interface PresignedUrlResponse {
  video_id: string;
  job_id: string;
  upload_url: string;
  expires_in: number;
}

export type PipelineStep =
  | "UPLOADED"
  | "QUEUED"
  | "EXTRACTING"
  | "FILTERING"
  | "DEDUPLICATING_FRAMES"
  | "READING_TEXT"
  | "EXTRACTING_DETAILS"
  | "GENERATING_IMAGES"
  | "FORMATTING"
  | "COMPLETED"
  | "FAILED";

export const PIPELINE_STEPS: { key: PipelineStep; label: string }[] = [
  { key: "EXTRACTING", label: "Extracting frames from video" },
  { key: "FILTERING", label: "Filtering blurry frames" },
  { key: "DEDUPLICATING_FRAMES", label: "Removing duplicate frames" },
  { key: "READING_TEXT", label: "Reading text from product labels" },
  { key: "EXTRACTING_DETAILS", label: "Extracting product details" },
  { key: "GENERATING_IMAGES", label: "Generating studio images" },
  { key: "FORMATTING", label: "Formatting catalog" },
];
