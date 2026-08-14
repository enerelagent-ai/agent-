from types import SimpleNamespace

from app.api.routes.dashboard import _attach_computed_fields
from app.schemas.dashboard import ComplexPriceSummary


def test_attach_computed_fields_keeps_complex_comparison_independent() -> None:
    listing = SimpleNamespace()
    complex_deal = {
        "complex_name": "Buti Town",
        "complex_deal_pct": 22.5,
        "complex_deal_status": "top_deal",
        "complex_deal_reason": None,
        "complex_n_comparable": 24,
        "complex_median_price_per_sqm": 4_000_000,
    }

    result = _attach_computed_fields(listing, None, complex_deal, None, None)

    assert result.deal_pct is None  # district comparison can be unavailable
    assert result.complex_name == "Buti Town"
    assert result.complex_deal_pct == 22.5
    assert result.complex_deal_status == "top_deal"
    assert result.complex_n_comparable == 24
    assert result.complex_median_price_per_sqm == 4_000_000.0


def test_complex_price_summary_schema_accepts_calculation_row() -> None:
    summary = ComplexPriceSummary.model_validate({
        "complex_id": 1,
        "complex_name": "Buti Town",
        "listing_type": "sale",
        "property_type": "Орон сууц зарна",
        "n_listings": 24,
        "avg_price": 300_000_000,
        "median_price": 290_000_000,
        "avg_price_per_sqm": 4_100_000,
        "median_price_per_sqm": 4_000_000,
        "n_with_price_per_sqm": 23,
    })
    assert summary.complex_name == "Buti Town"
    assert summary.n_listings == 24

