import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatDateSafe(dateStr) {
  if (!dateStr) return "Recent";
  try {
    const isoStr = String(dateStr).replace(" ", "T");
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) {
      return String(dateStr);
    }
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return "Recent";
  }
}
