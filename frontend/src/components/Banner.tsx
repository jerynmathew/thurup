// src/components/Banner.tsx
import React from "react";

export default function Banner({ type = "error", children }: { type?: "error" | "success" | string; children: React.ReactNode }) {
  const cls = type === "success" ? "banner banner--success" : "banner banner--error";
  return <div className={cls}>{children}</div>;
}
