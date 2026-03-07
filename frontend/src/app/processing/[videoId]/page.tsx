"use client";

import { useParams, useRouter } from "next/navigation";
import { useJobPoller } from "@/hooks/useJobPoller";
import { PIPELINE_STEPS, type PipelineStep } from "@/types";
import { useEffect } from "react";

const STEP_ORDER: PipelineStep[] = PIPELINE_STEPS.map((s) => s.key);

function getStepState(
  step: PipelineStep,
  currentStatus: PipelineStep
): "done" | "active" | "pending" | "failed" {
  if (currentStatus === "FAILED") {
    const currentIdx = STEP_ORDER.indexOf(step);
    const failedIdx = STEP_ORDER.indexOf(currentStatus);
    if (currentIdx < failedIdx) return "done";
    if (currentIdx === failedIdx) return "failed";
    return "pending";
  }
  if (currentStatus === "COMPLETED") return "done";

  const currentIdx = STEP_ORDER.indexOf(currentStatus);
  const stepIdx = STEP_ORDER.indexOf(step);

  if (stepIdx < currentIdx) return "done";
  if (stepIdx === currentIdx) return "active";
  return "pending";
}

export default function ProcessingPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;
  const { job, error } = useJobPoller(videoId);

  useEffect(() => {
    if (job?.status === "COMPLETED" && job.catalog_id) {
      const timer = setTimeout(() => {
        router.push(`/catalog/${videoId}`);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [job, videoId, router]);

  return (
    <div className="container page">
      <div className="page-header">
        <h1 className="page-title">Processing</h1>
        <p className="page-description">
          Video ID: {videoId}
          {job?.product_count
            ? ` \u2014 ${job.product_count} products found`
            : ""}
        </p>
      </div>

      {error && <div className="error-box" style={{ marginBottom: 16 }}>{error}</div>}

      <div className="card">
        <div className="steps">
          {PIPELINE_STEPS.map(({ key, label }) => {
            const state = job
              ? getStepState(key, job.status as PipelineStep)
              : "pending";
            return (
              <div key={key} className={`step ${state}`}>
                <div className="step-indicator">
                  {state === "done" ? "\u2713" : state === "failed" ? "\u2717" : ""}
                </div>
                <span>{label}</span>
              </div>
            );
          })}
        </div>

        {job?.status === "COMPLETED" && (
          <div style={{ marginTop: 20 }}>
            <span className="badge badge-success">Complete</span>
            <span
              style={{ marginLeft: 8, fontSize: 13, color: "var(--fg-muted)" }}
            >
              Redirecting to catalog...
            </span>
          </div>
        )}

        {job?.status === "FAILED" && (
          <div style={{ marginTop: 20 }}>
            <div className="error-box">
              {job.error_message || "Pipeline failed"}
            </div>
            <button
              className="btn btn-secondary"
              style={{ marginTop: 12 }}
              onClick={() => router.push("/")}
            >
              Back to upload
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
