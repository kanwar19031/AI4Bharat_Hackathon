"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CatalogResponse } from "@/types";

export default function ExportPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;

  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api
      .catalog(videoId)
      .then(setCatalog)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      );
  }, [videoId]);

  function handleDownload() {
    if (!catalog) return;
    const blob = new Blob(
      [JSON.stringify(catalog.ondc_catalog, null, 2)],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ondc-catalog-${videoId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleCopy() {
    if (!catalog) return;
    navigator.clipboard
      .writeText(JSON.stringify(catalog.ondc_catalog, null, 2))
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
  }

  if (error) {
    return (
      <div className="container page">
        <div className="error-box">{error}</div>
      </div>
    );
  }

  if (!catalog) {
    return (
      <div className="container page">
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="loader" />
          <span style={{ fontSize: 14, color: "var(--fg-muted)" }}>
            Loading...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="container page">
      <div className="page-header">
        <h1 className="page-title">Export Catalog</h1>
        <p className="page-description">ONDC-compliant catalog JSON</p>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
            textAlign: "center",
          }}
        >
          <div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>
              {catalog.products.length}
            </div>
            <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>
              Products
            </div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>
              {catalog.products.filter((p) => p.price).length}
            </div>
            <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>
              Priced
            </div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>
              <span className="badge badge-success">{catalog.status}</span>
            </div>
            <div style={{ fontSize: 13, color: "var(--fg-muted)", marginTop: 4 }}>
              Status
            </div>
          </div>
        </div>
      </div>

      <div className="toolbar">
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-primary" onClick={handleDownload}>
            Download JSON
          </button>
          <button className="btn btn-secondary" onClick={handleCopy}>
            {copied ? "Copied" : "Copy to clipboard"}
          </button>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => router.push(`/catalog/${videoId}`)}
        >
          Back to catalog
        </button>
      </div>

      <div className="code-block">
        {JSON.stringify(catalog.ondc_catalog, null, 2)}
      </div>
    </div>
  );
}
