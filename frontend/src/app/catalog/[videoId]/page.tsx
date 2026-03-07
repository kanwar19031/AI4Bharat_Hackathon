"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CatalogProduct, CatalogResponse } from "@/types";
import { ProductCard } from "@/components/ProductCard";
import { ProductEditModal } from "@/components/ProductEditModal";

export default function CatalogPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;

  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editProduct, setEditProduct] = useState<CatalogProduct | null>(null);

  useEffect(() => {
    api
      .catalog(videoId)
      .then((data) => {
        setCatalog(data);
        setProducts(data.products);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load catalog")
      );
  }, [videoId]);

  const handleDelete = useCallback((productId: string) => {
    setProducts((prev) => prev.filter((p) => p.product_id !== productId));
  }, []);

  const handleSave = useCallback(
    (updated: CatalogProduct) => {
      setProducts((prev) =>
        prev.map((p) => (p.product_id === updated.product_id ? updated : p))
      );
      setEditProduct(null);
    },
    []
  );

  async function handleSaveAll() {
    if (!catalog) return;
    setSaving(true);
    try {
      await api.updateCatalog(catalog.catalog_id, products);
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

  if (!catalog) {
    return (
      <div className="container page">
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="loader" />
          <span style={{ fontSize: 14, color: "var(--fg-muted)" }}>
            Loading catalog...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="container page">
      <div className="page-header">
        <h1 className="page-title">Product Catalog</h1>
        <p className="page-description">
          {products.length} products detected from video
        </p>
      </div>

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

      <div className="product-grid">
        {products.map((product) => (
          <ProductCard
            key={product.product_id}
            product={product}
            onEdit={() => setEditProduct(product)}
            onDelete={() => handleDelete(product.product_id)}
          />
        ))}
      </div>

      {products.length === 0 && (
        <div className="card" style={{ textAlign: "center" }}>
          <p style={{ color: "var(--fg-muted)" }}>No products found.</p>
        </div>
      )}

      {editProduct && (
        <ProductEditModal
          product={editProduct}
          onSave={handleSave}
          onCancel={() => setEditProduct(null)}
        />
      )}
    </div>
  );
}
