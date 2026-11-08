import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_profile", ROOT / "scripts/update_profile.py")
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "profile.json").read_text())
        self.data = {
            "username": "Gabriel7fs", "public_repos": 13, "stars": 0, "followers": 5,
            "language_bytes": {"TypeScript": 600, "HTML": 200, "CSS": 100, "C": 50, "Java": 50},
            "updated_at": "2026-11-08T12:00:00+00:00",
        }

    def test_pagination_and_ownership_do_not_include_forks_in_stars_or_languages(self):
        def repo(name, *, fork=False, private=False, stars=0):
            return {"name": name, "owner": {"login": "Gabriel7fs"}, "fork": fork,
                    "private": private, "stargazers_count": stars}
        first = [repo(f"fork-{i}", fork=True, stars=100) for i in range(99)] + [repo("project-one", stars=3)]
        second = [repo("project-two", stars=7), repo("Gabriel7fs"), repo("private", private=True, stars=50)]
        requested = []

        def api(path):
            requested.append(path)
            if path == "/users/Gabriel7fs":
                return {"login": "Gabriel7fs", "public_repos": 102, "followers": 5}
            if "/repos?" in path:
                return first if parse_qs(urlsplit(path).query)["page"] == ["1"] else second
            if path.endswith("/project-one/languages"):
                return {"TypeScript": 200, "HTML": 100}
            if path.endswith("/project-two/languages"):
                return {"TypeScript": 100, "C": 100}
            self.fail("Unexpected request: " + path)

        with patch.object(profile, "github_get", side_effect=api):
            result = profile.collect_data(self.config)
        self.assertEqual(result["public_repos"], 102)
        self.assertEqual(result["stars"], 10)
        self.assertEqual(result["language_bytes"], {"TypeScript": 300, "C": 100, "HTML": 100})
        self.assertEqual(result["language_repositories"], 2)
        self.assertTrue(any("page=2" in path for path in requested))

    def test_language_chart_includes_other_and_preserves_the_total(self):
        svg = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">' + profile.language_svg(self.data) + '</svg>')
        rectangles = svg.findall("{http://www.w3.org/2000/svg}rect")
        self.assertAlmostEqual(sum(float(rect.get("width")) for rect in rectangles), 1148, places=2)
        self.assertIn("Other", "".join(svg.itertext()))
        self.assertIn("10.0%", "".join(svg.itertext()))

    def test_profile_text_is_escaped_and_the_rendered_card_is_valid_svg(self):
        self.config["display_name"] = 'Gabriel & <script>alert("test")</script>'
        svg = profile.render_card(self.config, self.data)
        parsed = ET.fromstring(svg)
        self.assertEqual(parsed.findall(".//{http://www.w3.org/2000/svg}script"), [])
        self.assertIn("Gabriel &amp; &lt;script&gt;", svg)
        self.assertNotRegex(svg, r"\$[a-z_]+")

    def test_api_failure_keeps_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "profile.json").write_text(json.dumps(self.config))
            files = [root / "README.md", root / "assets/profile-card.svg", root / "assets/github-data.json"]
            for file in files:
                file.write_text("previous successful content")
            with patch.object(profile, "ROOT", root), patch.object(profile, "collect_data", side_effect=RuntimeError("API unavailable")), patch("sys.argv", ["update_profile.py"]):
                self.assertEqual(profile.main(), 1)
            self.assertTrue(all(file.read_text() == "previous successful content" for file in files))

    def test_readme_keeps_manual_content_outside_generated_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("My introduction\n" + profile.START + "\nold\n" + profile.END + "\nMy selected projects")
            with patch.object(profile, "ROOT", root):
                readme = profile.build_readme(self.config, self.data)
            self.assertTrue(readme.startswith("My introduction\n"))
            self.assertTrue(readme.endswith("\nMy selected projects"))
            self.assertIn("Java", readme)
            self.assertIn("Flutter", readme)


if __name__ == "__main__":
    unittest.main()
