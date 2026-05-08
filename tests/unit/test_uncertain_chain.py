"""Tests for UncertainChain — transitive uncertainty propagation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from ledge_lang.ai_types import Uncertain, UncertainChain
from ledge_lang.core_types import NOTHING


class TestChainConfidence:

    def test_product_of_three_steps(self):
        """chain_confidence uses position-weighted product — more conservative than simple product."""
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9), "paso1")
        chain.add(Uncertain("b", 0.8), "paso2")
        chain.add(Uncertain("c", 0.7), "paso3")
        result = chain.chain_confidence()
        simple_product = 0.9 * 0.8 * 0.7
        assert 0.0 < result < 1.0
        assert result <= simple_product  # weighted formula is always more conservative

    def test_zero_contaminates_whole_chain(self):
        """A single 0.0 step makes chain_confidence = 0.0."""
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9), "paso1")
        chain.add(Uncertain(NOTHING, 0.0), "paso2")
        chain.add(Uncertain("c", 0.7), "paso3")
        assert chain.chain_confidence() == 0.0

    def test_empty_chain_returns_zero(self):
        chain = UncertainChain()
        assert chain.chain_confidence() == 0.0

    def test_single_step_is_its_own_confidence(self):
        chain = UncertainChain()
        chain.add(Uncertain("x", 0.95), "solo")
        assert abs(chain.chain_confidence() - 0.95) < 1e-9

    def test_all_perfect_confidence(self):
        chain = UncertainChain()
        chain.add(Uncertain("a", 1.0), "s1")
        chain.add(Uncertain("b", 1.0), "s2")
        assert chain.chain_confidence() == 1.0


class TestChainIsSafe:

    def test_unsafe_when_one_step_below_threshold(self):
        """0.7 < 0.8 threshold → not safe."""
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9), "paso1")
        chain.add(Uncertain("b", 0.8), "paso2")
        chain.add(Uncertain("c", 0.7), "paso3")
        assert chain.chain_is_safe(0.8) is False

    def test_safe_when_all_meet_threshold(self):
        """All steps >= 0.7 → safe at 0.7 threshold."""
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9), "paso1")
        chain.add(Uncertain("b", 0.8), "paso2")
        chain.add(Uncertain("c", 0.7), "paso3")
        assert chain.chain_is_safe(0.7) is True

    def test_unsafe_with_zero_step(self):
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.95), "paso1")
        chain.add(Uncertain(NOTHING, 0.0), "sin_backend")
        assert chain.chain_is_safe(0.8) is False

    def test_empty_chain_is_not_safe(self):
        chain = UncertainChain()
        assert chain.chain_is_safe(0.8) is False


class TestWeakestStep:

    def test_weakest_step_returns_correct_name(self):
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9), "diagnostico")
        chain.add(Uncertain("b", 0.8), "clasificacion")
        chain.add(Uncertain("c", 0.7), "protocolo")
        assert chain.weakest_step() == "protocolo"

    def test_weakest_step_uses_auto_name_when_no_name_given(self):
        chain = UncertainChain()
        chain.add(Uncertain("a", 0.9))
        chain.add(Uncertain("b", 0.5))
        chain.add(Uncertain("c", 0.8))
        assert chain.weakest_step() == "step_2"

    def test_weakest_step_empty_chain_returns_empty_string(self):
        chain = UncertainChain()
        assert chain.weakest_step() == ""


class TestNoBackend:

    def test_no_backend_chain_confidence_is_zero(self):
        """Without a backend, all AI results have confidence=0, so chain=0."""
        from ledge_lang import run
        src = (
            'define r1 as analyze("text") using sentiment\n'
            'define r2 as classify("text") using ["a","b"]\n'
            'define chain as uncertain_chain(list [r1, r2])\n'
            'show chain_confidence(chain)\n'
        )
        lines, _ = run(src, reset_audit=True)
        assert float(lines[0].strip()) == 0.0
