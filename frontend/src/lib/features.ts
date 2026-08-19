function enabled(value: string | undefined): boolean {
  return value?.trim().toLowerCase() === "true";
}

// Server-side marketplace navigation switch. Complex insights are gated by
// the backend's COMPLEX_INSIGHTS_ENABLED setting so every API consumer sees
// the same policy; keeping a second unused frontend copy would be misleading.
export const marketplaceV2Enabled = enabled(
  process.env.MARKETPLACE_V2_ENABLED,
);
