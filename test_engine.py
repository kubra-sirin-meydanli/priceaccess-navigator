from engine import run_cascade, compute_binding_ceiling, prices, baskets

def test_spain_cascade():
    result = run_cascade("ES", 400, prices, baskets)
    assert result["ES"] == 400
    assert result["FR"] == 460
    assert result["NL"] == 542
    assert result["DE"] == 1164
    assert result["UK"] == 700
    assert result["TR"] == 195

def test_german_trigger_no_cascade():
    # A German cut is self-contained — nobody else moves
    result = run_cascade("DE", 930, prices, baskets)
    assert result["DE"] == 930
    assert result["FR"] == 620
    assert result["NL"] == 582
    assert result["UK"] == 700
    assert result["ES"] == 560
    assert result["TR"] == 195


def test_no_market_rises():
    # A mandated cut can never raise any price
    result = run_cascade("ES", 400, prices, baskets)
    for market in baskets:
        assert result[market] <= prices[market]


def test_pre_shock_ceilings():
    # The ceiling function reproduces the Excel pre-shock ceilings
    assert compute_binding_ceiling("FR", prices, baskets) == 560
    assert compute_binding_ceiling("NL", prices, baskets) == 650
    assert compute_binding_ceiling("DE", prices, baskets) is None