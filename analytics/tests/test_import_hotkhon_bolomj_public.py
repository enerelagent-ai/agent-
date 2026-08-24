import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "import_hotkhon_bolomj_public.py"
SPEC = importlib.util.spec_from_file_location("import_hotkhon_bolomj_public", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_extract_affordability_data():
    html = '''<p>Өгөгдөл: 2026-08-24</p><script>
    var L = [[41,155,1],[80,200,0]], D = ["Хан-Уул","Баянзүрх"], CAP = 150000000, MIN_DOWN = 0.3, MAX_AREA = 80.0;
    </script>'''
    data = MODULE.extract_affordability_data(html)
    assert data.data_as_of == "2026-08-24"
    assert data.listings == [[41, 155, 1], [80, 200, 0]]
    assert data.districts == ["Хан-Уул", "Баянзүрх"]
    assert data.rules["loan_cap_mnt"] == 150_000_000
    assert data.rules["min_downpayment_ratio"] == 0.3
    assert data.rules["max_area_sqm"] == 80.0


def test_extract_rejects_invalid_district_index():
    html = '''<script>var L=[[41,155,2]],D=["Хан-Уул"],CAP=150000000,MIN_DOWN=0.3,MAX_AREA=80;</script>'''
    try:
        MODULE.extract_affordability_data(html)
    except ValueError as exc:
        assert "invalid affordability" in str(exc)
    else:
        raise AssertionError("invalid tuple should fail")
