const API_URL = "http://localhost:8000";

interface DistrictInvestmentSummary {
  district: string;
  avg_sale_price: number;
  gross_rental_yield_pct: number;
  roi_pct: number;
}

async function getInvestmentSummary(): Promise<DistrictInvestmentSummary[]> {
  const res = await fetch(`${API_URL}/dashboard/investment-summary`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`/dashboard/investment-summary returned ${res.status}`);
  }
  return res.json();
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-US").format(Math.round(value));
}

export default async function Home() {
  const rows = await getInvestmentSummary();

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Дүүргийн хөрөнгө оруулалтын үзүүлэлт</h1>
      <table style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={cellStyle}>Дүүрэг</th>
            <th style={cellStyle}>Дундаж зарах үнэ</th>
            <th style={cellStyle}>Түрээсийн өгөөж (%)</th>
            <th style={cellStyle}>ROI (%)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.district}>
              <td style={cellStyle}>{row.district}</td>
              <td style={cellStyle}>{formatPrice(row.avg_sale_price)}</td>
              <td style={cellStyle}>{row.gross_rental_yield_pct.toFixed(2)}</td>
              <td style={cellStyle}>{row.roi_pct.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

const cellStyle = { border: "1px solid #ccc", padding: "6px 12px" };
