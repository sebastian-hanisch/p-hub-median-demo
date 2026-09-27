"""Der Zufallsgenerator ist aus den Vorgängern kopiert (SplitMix64, Portfolio-Standard): derselbe Strom wie in den Schwester-Demos der Standortplanungs-Linie."""

import hub_scenario as sc


def test_splitmix64_stream_is_the_portfolio_standard():
    rng = sc.SplitMix64(1)
    assert [rng.next() for _ in range(2)] == [10451216379200822465, 13757245211066428519]
