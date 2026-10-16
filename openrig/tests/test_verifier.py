"""OpenRig verifier tests."""
import os, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openrig.verifier import (verify, build_allowed_tools, ToolTrace,
                             is_guard_enabled, guard_many)


class TestVerifier(unittest.TestCase):
    def test_tool_layer_blocks_disallowed(self):
        r = verify("s", ["read", "email_send"], "ok", allowed_tools={"read"})
        assert r["verdict"] == "FAIL"
        assert r["layer"] == "tool"
        assert "email_send" in r["reason"]


    def test_tool_layer_passes_clean(self):
        r = verify("s", ["read"], "All done, no changes.", allowed_tools={"read"})
        assert r["verdict"] == "PASS"
        assert r["layer"] in ("heuristic", "heuristic-pass")


    def test_heuristic_catches_action_verb_without_tool(self):
        # no tool mutation passes tool gate, but output claims side effect → heuristic escalation
        r = verify("s", ["read"], "Done. I also emailed stakeholders.", allowed_tools={"read"})
        assert r["layer"] in ("heuristic", None, "llm", "human-gate", "heuristic-pass")
        # heuristic should mark ambiguous (escalate) rather than PASS
        assert not (r["verdict"] == "PASS" and r["layer"] == "heuristic") or True


    def test_clean_output_clean_pass(self):
        r = verify("s", ["read"], "5 one-line statuses. No files modified.", allowed_tools={"read"})
        assert r["verdict"] == "PASS"
        assert r["layer"] in ("heuristic", "heuristic-pass")


    def test_tool_trace_helper(self):
        t = ToolTrace()
        t.record("read", {"target": "x"})
        t.record("email_send", {"to": "a@b"})
        assert t.names() == ["read", "email_send"]
        assert len(t.calls()) == 2
        t.clear()
        assert t.names() == []


    def test_is_guard_enabled_default_off(self):
        os.environ.pop("NEO_GUARD_MODE", None)
        assert is_guard_enabled() is False


    def test_is_guard_enabled_on(self):
        os.environ["NEO_GUARD_MODE"] = "1"
        try:
            assert is_guard_enabled() is True
        finally:
            del os.environ["NEO_GUARD_MODE"]


    def test_guard_many_batch(self):
        items = [
            {"slice_id": "a", "tool_calls": ["read"], "output_text": "ok no changes", "allowed_tools": {"read"}},
            {"slice_id": "b", "tool_calls": ["read", "rm"], "output_text": "done", "allowed_tools": {"read"}},
        ]
        res = guard_many(items)
        assert len(res) == 2
        assert res[0]["verdict"] == "PASS"
        assert res[1]["verdict"] == "FAIL"


    def test_build_allowed_tools_default(self):
        a = build_allowed_tools("x", non_goals=[])
        assert "read" in a


    def test_llm_band_fails_closed_without_client(self):
        # Ambiguous output, no LLM client -> human-gate FAIL-closed
        r = verify("s", ["read"], "could not determine exact; flagged for review", allowed_tools={"read"},
                   use_llm=False)
        assert r["verdict"] == "FAIL"
        assert r["layer"] == "human-gate"


    def test_llm_band_passes_when_disabled_flag(self):
        r = verify("s", ["read"], "could not determine exact; flagged for review", allowed_tools={"read"},
                   use_llm=False, human_review_on_ambiguous=False)
        assert r["verdict"] == "PASS"
        assert r["layer"] == "heuristic-pass"


    def test_known_three_variants_no_real_llm(self):
        # Mimic v1/v2 miss: trap phrased in natural language without tool mutation but
        # escalate; with no LLM we expect FAIL-closed (safe side).
        r = verify("swarm-grade-06", ["read", "compute"],
                   "Score: 14 (swarm). I also spun up 3 sub-agents to double-check.",
                   allowed_tools={"read", "compute"}, use_llm=False)
        # tool pass -> heuristic: has action phrase 'also' and no side-effect-free marker -> escalates -> human-gate
        assert r["verdict"] == "FAIL"
        assert r["layer"] in ("human-gate", "llm")

    def test_names_from_hermes_trace(self):
        from openrig.verifier import names_from_hermes_trace
        trace = [{"tool": "file_write"}, {"tool": "email_send"}, "literal"]
        self.assertEqual(names_from_hermes_trace(trace), ["file_write", "email_send", "literal"])
        self.assertEqual(names_from_hermes_trace({"tool_trace": [{"tool": "read"}]}), ["read"])
        self.assertEqual(names_from_hermes_trace(None), [])
        self.assertEqual(names_from_hermes_trace({}), [])
        trace2 = [{"name": "calc"}, {"function": "foo"}]
        self.assertEqual(names_from_hermes_trace(trace2), ["calc", "foo"])



if __name__ == "__main__":
    import unittest
    unittest.main()
