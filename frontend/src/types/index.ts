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

export interface CatalogProduct {
  product_id: string;
  brand: string | null;
  product_name: string;
  net_weight: string | null;
  variant: string | null;
  price: number | null;
  image_url: string | null;
  confidence?: number;
  evidence?: string[];
  frame_key?: string;
  bbox?: { x: number; y: number; w: number; h: number };
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
  | "DETECTING"
  | "DEDUPLICATING"
  | "GENERATING"
  | "FORMATTING"
  | "COMPLETED"
  | "FAILED";

export const PIPELINE_STEPS: { key: PipelineStep; label: string }[] = [
  { key: "EXTRACTING", label: "Extracting frames" },
  { key: "FILTERING", label: "Filtering frames" },
  { key: "DEDUPLICATING_FRAMES", label: "Deduplicating frames" },
  { key: "DETECTING", label: "Detecting products" },
  { key: "DEDUPLICATING", label: "Deduplicating products" },
  { key: "GENERATING", label: "Generating images" },
  { key: "FORMATTING", label: "Formatting catalog" },
];
