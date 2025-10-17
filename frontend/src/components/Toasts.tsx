// src/components/Toasts.tsx
import React from "react";

export type ToastItem = { id: string; message: string; kind?: "info" | "success" | "error" };
export default function Toasts({ items }: { items: ToastItem[] }) {
  return (
    <div className="toast-wrap">
      {items.map(t => (
        <div key={t.id} className={`toast toast--${t.kind || "info"}`}>{t.message}</div>
      ))}
    </div>
  );
}
