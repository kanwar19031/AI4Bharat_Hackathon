"use client";

import { useState } from "react";
import type { CatalogProduct } from "@/types";

interface ProductEditModalProps {
  product: CatalogProduct;
  onSave: (updated: CatalogProduct) => void;
  onCancel: () => void;
}

export function ProductEditModal({
  product,
  onSave,
  onCancel,
}: ProductEditModalProps) {
  const [form, setForm] = useState({
    brand: product.brand || "",
    product_name: product.product_name,
    net_weight: product.net_weight || "",
    variant: product.variant || "",
    price: product.price?.toString() || "",
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSave({
      ...product,
      brand: form.brand || null,
      product_name: form.product_name,
      net_weight: form.net_weight || null,
      variant: form.variant || null,
      price: form.price ? parseFloat(form.price) : null,
    });
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSubmit}
      >
        <div className="modal-title">Edit Product</div>

        <div className="input-group">
          <label className="input-label">Brand</label>
          <input
            className="input"
            value={form.brand}
            onChange={(e) => handleChange("brand", e.target.value)}
            placeholder="e.g. Doritos"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Product Name</label>
          <input
            className="input"
            value={form.product_name}
            onChange={(e) => handleChange("product_name", e.target.value)}
            required
          />
        </div>

        <div className="input-group">
          <label className="input-label">Net Weight</label>
          <input
            className="input"
            value={form.net_weight}
            onChange={(e) => handleChange("net_weight", e.target.value)}
            placeholder="e.g. 100g"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Variant</label>
          <input
            className="input"
            value={form.variant}
            onChange={(e) => handleChange("variant", e.target.value)}
            placeholder="e.g. Sweet Chili"
          />
        </div>

        <div className="input-group">
          <label className="input-label">Price (INR)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            value={form.price}
            onChange={(e) => handleChange("price", e.target.value)}
            placeholder="0.00"
          />
        </div>

        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary btn-sm">
            Save
          </button>
        </div>
      </form>
    </div>
  );
}
