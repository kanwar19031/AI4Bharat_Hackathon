import type {
  CatalogProduct,
  CatalogResponse,
  JobStatusResponse,
  ProcessJobResponse,
  UpdateCatalogResponse,
  UseSampleResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5001";
const API_PREFIX = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /** Upload a video file through the backend (proxied to S3). */
  async uploadVideo(
    file: File,
    onProgress?: (pct: number) => void
  ): Promise<{ video_id: string; job_id: string }> {
    const formData = new FormData();
    formData.append("file", file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}${API_PREFIX}/upload/video`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          resolve({ video_id: data.video_id, job_id: data.job_id });
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.responseText}`));
        }
      };
      xhr.onerror = () => reject(new Error("Upload network error"));
      xhr.send(formData);
    });
  },

  useSample(): Promise<UseSampleResponse> {
    return request("/jobs/use-sample", { method: "POST" });
  },

  process(videoId: string): Promise<ProcessJobResponse> {
    return request(`/jobs/${videoId}/process`, { method: "POST" });
  },

  status(videoId: string): Promise<JobStatusResponse> {
    return request(`/jobs/${videoId}/status`);
  },

  catalog(videoId: string): Promise<CatalogResponse> {
    return request(`/jobs/${videoId}/catalog`);
  },

  updateCatalog(
    catalogId: string,
    products: CatalogProduct[]
  ): Promise<UpdateCatalogResponse> {
    return request(`/catalogs/${catalogId}`, {
      method: "PUT",
      body: JSON.stringify({ products }),
    });
  },
};
