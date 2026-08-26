import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "import_hotkhon_public.py"
SPEC = importlib.util.spec_from_file_location("import_hotkhon_public", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_extract_profile_metrics_reads_factual_fields():
    html = '''
    <div class="sub">2013 онд ашиглалтад орсон · 9 давхар</div>
    <div class="v">200–603 <small>сая ₮</small></div><div class="k">Үнийн хүрээ</div>
    <div class="v">7.4 <small>/ 10</small></div><div class="k">Байршлын оноо</div>
    <span class="rng">2026-06-24 — 2026-08-22</span>
    <h2>Өрөөний тоогоор</h2><table><tr><td>1 өрөө</td><td class="r">6.49</td></tr></table>
    <h2>Байршлын задаргаа</h2>
    <div class="lab"><span>Худалдаа, үйлчилгээ</span><span class="num">9.4</span></div>
    <h2>Зах зээлийн байдал</h2>
    <div class="v">10 <small>хоног</small></div><div class="k">Зар цэвэрлэгдэх</div>
    <div class="v warn">8</div><div class="k">Үнээ бууруулсан</div>
    <div class="v">7.1%</div><div class="k">Түрээсийн өгөөж</div>
    <h2>Үнэд нөлөөлж буй хүчин зүйл</h2>
    <span class="lab">Байршил</span><span class="val pos">+17.8%</span>
    <span class="lab">Барилгын он</span><span class="val neg">−6.5%</span>
    <h2>Байрны бүтэц</h2>
    '''
    metrics = MODULE.extract_profile_metrics(html)
    assert metrics["building_summary"] == "2013 онд ашиглалтад орсон · 9 давхар"
    assert metrics["price_range_million"] == [200.0, 603.0]
    assert metrics["location_score"] == 7.4
    assert metrics["clearance_days"] == 10
    assert metrics["price_reductions_14d"] == 8
    assert metrics["rental_yield_pct"] == 7.1
    assert metrics["room_price_per_sqm_million"] == [{"rooms": 1, "value": 6.49}]
    assert metrics["location_breakdown"] == [{"label": "Худалдаа, үйлчилгээ", "score": 9.4}]
    assert metrics["price_drivers"] == [
        {"label": "Байршил", "impact_pct": 17.8},
        {"label": "Барилгын он", "impact_pct": -6.5},
    ]
