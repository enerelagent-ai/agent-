export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(Math.round(value));
}

export function formatMnt(value: number): string {
  return `${formatNumber(value)}₮`;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}
