"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFileSelect(file: File) {
    if (!file.type.startsWith("video/")) {
      setError("Please select a video file (MP4, MOV, etc.).");
      return;
    }
    setError(null);
    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setUploading(true);
    setUploadProgress(0);
    setError(null);
    try {
      const { video_id } = await api.uploadVideo(selectedFile, (pct) =>
        setUploadProgress(pct)
      );
      setUploadProgress(100);
      await api.process(video_id);
      router.push(`/processing/${video_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploading(false);
    }
  }

  async function handleUseSample() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.useSample();
      await api.process(res.video_id);
      router.push(`/processing/${res.video_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start pipeline");
      setLoading(false);
    }
  }

  return (
    <div className="container page">
      <div className="page-header">
        <h1 className="page-title">Upload Store Video</h1>
        <p className="page-description">
          Record a short video of your store shelves and upload it to generate a
          product catalog automatically.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div
          className={`upload-zone ${dragOver ? "upload-zone--dragover" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files?.[0];
            if (file) handleFileSelect(file);
          }}
          onClick={() => fileInputRef.current?.click()}
          style={{ cursor: uploading ? "default" : "pointer" }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelect(file);
            }}
          />

          {selectedFile ? (
            <>
              <div className="upload-zone-title">
                📹 {selectedFile.name}
              </div>
              <div className="upload-zone-hint">
                {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
                {!uploading && " — Click to change file"}
              </div>

              {uploading && (
                <div style={{ width: "100%", maxWidth: 320, marginTop: 12 }}>
                  <div
                    style={{
                      height: 6,
                      borderRadius: 3,
                      background: "var(--bg-muted)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${uploadProgress}%`,
                        background: "var(--accent)",
                        borderRadius: 3,
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--fg-muted)",
                      textAlign: "center",
                      marginTop: 4,
                    }}
                  >
                    Uploading… {uploadProgress}%
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="upload-zone-title">
                {dragOver ? "Drop video here" : "Video upload"}
              </div>
              <div className="upload-zone-hint">
                Drag and drop an MP4 file, or click to browse.
              </div>
            </>
          )}
        </div>

        {selectedFile && !uploading && (
          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button className="btn btn-primary" onClick={handleUpload}>
              Upload &amp; process
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
            >
              Clear
            </button>
          </div>
        )}
      </div>

      <div className="divider" />

      <div className="card">
        <h2 style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>
          Quick Start
        </h2>
        <p style={{ fontSize: 14, color: "var(--fg-muted)", marginBottom: 16 }}>
          Use the built-in sample video to test the pipeline without uploading.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleUseSample}
          disabled={loading || uploading}
        >
          {loading && <span className="loader" />}
          {loading ? "Starting..." : "Use sample video"}
        </button>
      </div>

      {error && (
        <div className="error-box" style={{ marginTop: 16 }}>
          {error}
        </div>
      )}
    </div>
  );
}
