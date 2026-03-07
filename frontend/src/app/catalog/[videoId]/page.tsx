"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CatalogProduct, CatalogResponse } from "@/types";

export default function CatalogPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;

  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [product, setProduct] = useState<CatalogProduct | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeImageIdx, setActiveImageIdx] = useState(0);

  useEffect(() => {
    api
      .catalog(videoId)
      .then((data) => {
        setCatalog(data);
        if (data.products.length > 0) {
          setProduct(data.products[0]);
        }
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load catalog")
      );
  }, [videoId]);

  async function handleSaveAll() {
    if (!catalog || !product) return;
    setSaving(true);
    try {
      await api.updateCatalog(catalog.catalog_id, [product]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <div className="container page">
        <div className="error-box">{error}</div>
        <button
          className="btn btn-secondary"
          style={{ marginTop: 12 }}
          onClick={() => router.push("/")}
        >
          Back to upload
        </button>
      </div>
    );
  }

  if (!catalog || !product) {
    return (
      <div className="container page">
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="loader" />
          <span style={{ fontSize: 14, color: "var(--fg-muted)" }}>
            Loading product details...
          </span>
        </div>
      </div>
    );
  }

  const images = product.images || [];
  const nutritionFacts = product.nutrition_facts;
  const nutritionEntries = nutritionFacts
    ? Object.entries(nutritionFacts).filter(([, v]) => v != null)
    : [];

  return (
    <div className="container page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">
          {product.brand ? `${product.brand} — ` : ""}
          {product.product_name}
        </h1>
        {product.description && (
          <p className="page-description">{product.description}</p>
        )}
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn btn-primary"
            onClick={handleSaveAll}
            disabled={saving}
          >
            {saving && <span className="loader" />}
            {saving ? "Saving..." : "Save changes"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => router.push(`/export/${videoId}`)}
          >
            Export ONDC JSON
          </button>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => router.push("/")}
        >
          New video
        </button>
      </div>

      {/* Main content: two columns */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: images.length > 0 ? "1fr 1fr" : "1fr",
          gap: 24,
          marginTop: 16,
        }}
      >
        {/* Left: Image gallery */}
        {images.length > 0 && (
          <div className="card">
            <div style={{ marginBottom: 12 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                Product Images ({images.length})
              </h3>
              <p style={{ fontSize: 12, color: "var(--fg-muted)" }}>
                {images[activeImageIdx]?.frame_type || "unknown"} view
              </p>
            </div>
            <div
              style={{
                width: "100%",
                aspectRatio: "1/1",
                borderRadius: 8,
                overflow: "hidden",
                background: "#f5f5f5",
                border: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={images[activeImageIdx]?.image_url || ""}
                alt={`${product.product_name} - ${images[activeImageIdx]?.frame_type}`}
                style={{
                  maxWidth: "100%",
                  maxHeight: "100%",
                  objectFit: "contain",
                }}
              />
            </div>

            {/* Thumbnail strip */}
            {images.length > 1 && (
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  marginTop: 12,
                  overflowX: "auto",
                }}
              >
                {images.map((img, idx) => (
                  <button
                    key={img.image_id}
                    onClick={() => setActiveImageIdx(idx)}
                    style={{
                      width: 64,
                      height: 64,
                      borderRadius: 6,
                      overflow: "hidden",
                      border:
                        idx === activeImageIdx
                          ? "2px solid var(--primary)"
                          : "1px solid var(--border)",
                      background: "#f5f5f5",
                      cursor: "pointer",
                      flexShrink: 0,
                      padding: 0,
                    }}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={img.image_url}
                      alt={img.frame_type || `View ${idx + 1}`}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Right: Product details */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Basic info card */}
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Basic Information
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <DetailItem label="Brand" value={product.brand} />
              <DetailItem label="Product Name" value={product.product_name} />
              <DetailItem label="Variant" value={product.variant} />
              <DetailItem label="Category" value={product.category} />
              <DetailItem label="Net Weight" value={product.net_weight} />
              <DetailItem
                label="MRP"
                value={product.price ? `₹${product.price}` : null}
              />
              <DetailItem label="Barcode" value={product.barcode} />
              <DetailItem label="Shelf Life" value={product.shelf_life} />
            </div>
          </div>

          {/* Tags */}
          {product.tags && product.tags.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                Tags
              </h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {product.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      padding: "3px 10px",
                      borderRadius: 20,
                      background: "var(--primary-light, #e8f4ff)",
                      color: "var(--primary, #3b82f6)",
                      fontSize: 12,
                      fontWeight: 500,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Manufacturer / FSSAI */}
          {(product.manufacturer || product.fssai_license) && (
            <div className="card">
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
                Manufacturer Details
              </h3>
              <DetailItem label="Manufacturer" value={product.manufacturer} />
              <DetailItem
                label="FSSAI License"
                value={product.fssai_license}
              />
            </div>
          )}
        </div>
      </div>

      {/* Ingredients (full width) */}
      {product.ingredients && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
            Ingredients
          </h3>
          <p style={{ fontSize: 13, color: "var(--fg-muted)", lineHeight: 1.6 }}>
            {product.ingredients}
          </p>
        </div>
      )}

      {/* Nutrition Facts */}
      {nutritionEntries.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
            Nutrition Facts
          </h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
              gap: 8,
            }}
          >
            {nutritionEntries.map(([key, value]) => (
              <div
                key={key}
                style={{
                  padding: "8px 12px",
                  background: "var(--bg-card, #fafafa)",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--fg-muted)",
                    textTransform: "capitalize",
                  }}
                >
                  {key.replace(/_/g, " ")}
                </div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div style={{ marginBottom: 4 }}>
      <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 14, fontWeight: value ? 500 : 400 }}>
        {value || (
          <span style={{ color: "var(--fg-muted)", fontStyle: "italic" }}>
            Not detected
          </span>
        )}
      </div>
    </div>
  );
}
