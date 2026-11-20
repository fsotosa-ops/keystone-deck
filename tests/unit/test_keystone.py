"""Unit tests for the keystone core CLI. Run: python3 -m unittest discover tests/unit"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "keystone"
CLI = PLUGIN / "scripts" / "keystone.py"
sys.path.insert(0, str(PLUGIN / "scripts"))

from ks import brand, contrast, deck, evidence, talk  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True)


class Contrast(unittest.TestCase):
    def test_black_on_white_is_21(self):
        self.assertAlmostEqual(contrast.ratio("#000000", "#FFFFFF"), 21.0, places=1)

    def test_thresholds(self):
        rows = contrast.check_pairs({"a": "#777777", "b": "#FFFFFF"}, [["a", "b"], ["a", "b", "large"]])
        self.assertFalse(rows[0]["ok"])   # 4.48:1 fails normal text
        self.assertTrue(rows[1]["ok"])    # passes large text


class Presets(unittest.TestCase):
    def test_every_preset_loads_and_passes_contrast(self):
        for d in sorted((PLUGIN / "presets").iterdir()):
            with self.subTest(preset=d.name):
                b = brand.load(d / "brand.json")
                rows = contrast.check_pairs(b["color"], b["textPairs"])
                self.assertTrue(rows, "presets must declare textPairs")
                self.assertTrue(all(r["ok"] for r in rows), [r for r in rows if not r["ok"]])

    def test_compile_writes_all_targets(self):
        with tempfile.TemporaryDirectory() as t:
            r = run("brand", "compile", "preset:ink", "-o", t)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for name in ("brand.css", "brand.gs", "theme.ts", "palette.py", "brand-sheet.html"):
                self.assertTrue((Path(t) / name).exists(), name)
            css = (Path(t) / "brand.css").read_text()
            self.assertIn("--ks-accent:", css)
            self.assertIn("--ks-accent-inverse:", css)
            ns = {}
            exec((Path(t) / "palette.py").read_text(), ns)
            self.assertEqual(ns["COLOR"]["accent"], "#D2381E")

    def test_low_contrast_brand_is_refused(self):
        src = json.loads((PLUGIN / "presets" / "neutral" / "brand.json").read_text())
        src["color"]["muted"]["$value"] = "#C8C8C8"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "brand.json"
            p.write_text(json.dumps(src))
            self.assertEqual(run("brand", "check", str(p)).returncode, 1)
            self.assertEqual(run("brand", "compile", str(p), "-o", t).returncode, 1)

    def test_alias_resolution(self):
        src = json.loads((PLUGIN / "presets" / "neutral" / "brand.json").read_text())
        src["color"]["on-highlight"]["$value"] = "{color.ink}"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "brand.json"
            p.write_text(json.dumps(src))
            self.assertEqual(brand.load(p)["color"]["on-highlight"], src["color"]["ink"]["$value"])

    def test_missing_role_is_an_error(self):
        src = json.loads((PLUGIN / "presets" / "neutral" / "brand.json").read_text())
        del src["color"]["accent"]
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "brand.json"
            p.write_text(json.dumps(src))
            with self.assertRaises(brand.BrandError):
                brand.load(p)


TALK = """# T
**Audience:** a board deciding on a pilot.
**Thread:** one sentence.

## a · Ana · 0:20
**En la lámina:** x
Hola a todos.
**Pasa a:** ¿y entonces?

## b · Ben · 0:10
**On slide:** y
Closing words. **Click:** reveal.

# Appendix
## extra
Backup text.
"""


class Talk(unittest.TestCase):
    def parse(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(text)
        return talk.parse(f.name)

    def test_bilingual_labels_timing_and_appendix(self):
        doc = self.parse(TALK)
        self.assertEqual([s["id"] for s in doc["slides"]], ["a", "b", "extra"])
        self.assertEqual(doc["slides"][0]["leads_to"], "¿y entonces?")
        self.assertEqual(doc["slides"][1]["clicks"], 1)
        self.assertTrue(doc["slides"][2]["appendix"])
        self.assertEqual(talk.summary(doc)["seconds"], 30)
        errors, _ = talk.check(doc, ["a", "b", "extra"])
        self.assertEqual(errors, [])

    def test_missing_leads_to_and_notes(self):
        doc = self.parse(TALK.replace("**Pasa a:** ¿y entonces?", ""))
        errors, _ = talk.check(doc, ["a", "b", "c"])
        self.assertTrue(any("Leads to" in e for e in errors))
        self.assertTrue(any("without notes: c" in e for e in errors))


class DeckAndEvidence(unittest.TestCase):
    DECK = {"meta": {"title": "x", "brand": "preset:neutral"}, "slides": [
        {"id": "s1", "layout": "figures", "kicker": "K", "title": "People rarely get the help they need",
         "figures": [{"value": "{{fig:f1}}", "label": "get help {{ref:r1}}"}]},
        {"id": "s2", "layout": "cards", "kicker": "K", "title": "Market", "highlight": [0, 1],
         "items": [{"title": "We saw 340 users"}]},
    ]}
    LEDGER = {"figures": {"f1": {"value": 0.4, "display": "40%", "tier": "V", "source": "r1"},
                          "f2": {"value": 1, "tier": "P"}},
              "refs": {"r1": {"text": "Org. (2025). Report."}}}

    def test_deck_rules(self):
        errors, warnings = deck.check(self.DECK)
        self.assertTrue(any("highlighted" in e for e in errors))
        self.assertTrue(any("reads like a label" in w for w in warnings))

    def test_evidence_rules(self):
        errors, warnings = evidence.check(self.LEDGER, self.DECK)
        self.assertTrue(any("f2: tier P" in e for e in errors))
        self.assertTrue(any("'340'" in w for w in warnings))
        self.assertTrue(any("f2 is never shown" in w for w in warnings))

    def test_resolve_numbers_refs(self):
        out = evidence.resolve(self.DECK, self.LEDGER)
        s1 = out["slides"][0]
        self.assertEqual(s1["figures"][0]["value"], "40%")
        self.assertEqual(s1["figures"][0]["label"], "get help [1]")
        self.assertEqual(s1["_sources"], [(1, "Org. (2025). Report.")])
        self.assertEqual(s1["_tiers"], ["V"])


class Scaffold(unittest.TestCase):
    def test_new_then_check_passes(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "deck"
            self.assertEqual(run("new", str(d), "--title", "X", "--brand", "preset:warm").returncode, 0)
            r = run("check", str(d))
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(run("resolve", str(d)).returncode, 0)
            self.assertTrue((d / "build" / "deck.resolved.json").exists())

    def test_new_refuses_nonempty(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "x").write_text("x")
            self.assertEqual(run("new", t).returncode, 1)


class Manifests(unittest.TestCase):
    def test_marketplace_points_to_real_plugins(self):
        m = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        for p in m["plugins"]:
            manifest = ROOT / p["source"] / ".claude-plugin" / "plugin.json"
            self.assertTrue(manifest.exists(), manifest)
            pj = json.loads(manifest.read_text())
            self.assertEqual(pj["name"], p["name"])
            self.assertEqual(pj["version"], p["version"])

    def test_skills_have_frontmatter(self):
        for s in (PLUGIN / "skills").iterdir():
            text = (s / "SKILL.md").read_text()
            self.assertTrue(text.startswith("---\nname: " + s.name + "\n"), s.name)
            self.assertRegex(text, r"\ndescription: Use (when|after) ")


if __name__ == "__main__":
    unittest.main()
