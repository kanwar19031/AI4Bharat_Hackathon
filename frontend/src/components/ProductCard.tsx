import type { CatalogProduct } from "@/types";

interface ProductCardProps {
  product: CatalogProduct;
  onEdit: () => void;
  onDelete: () => void;
}

export function ProductCard({ product, onEdit, onDelete }: ProductCardProps) {
  return (
    <div className="product-card">
      {product.brand && (
        <div className="product-card-brand">{product.brand}</div>
      )}
      <div className="product-card-name">{product.product_name}</div>
      {product.net_weight && (
        <div className="product-card-meta">{product.net_weight}</div>
      )}
      {product.confidence !== undefined && (
        <div className="product-card-meta">
          Confidence: {(product.confidence * 100).toFixed(0)}%
        </div>
      )}
      {product.price !== null && product.price !== undefined && (
        <div style={{ fontSize: 15, fontWeight: 600 }}>
          INR {product.price.toFixed(2)}
        </div>
      )}
      <div className="product-card-actions">
        <button className="btn btn-secondary btn-sm" onClick={onEdit}>
          Edit
        </button>
        <button className="btn btn-danger btn-sm" onClick={onDelete}>
          Remove
        </button>
      </div>
    </div>
  );
}
