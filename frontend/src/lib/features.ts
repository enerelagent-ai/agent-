function enabled(value: string | undefined): boolean {
  return value?.trim().toLowerCase() === "true";
}

// Server-side release switches. Both default to false so a deployment can
// roll back navigation/insights without reverting code or changing data.
export const marketplaceV2Enabled = enabled(
  process.env.MARKETPLACE_V2_ENABLED,
);
export const complexInsightsEnabled = enabled(
  process.env.COMPLEX_INSIGHTS_ENABLED,
);
