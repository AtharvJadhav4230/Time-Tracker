from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from timetracker.categories import CategoryConfigError, load_categorizer


class CategorizerTests(unittest.TestCase):
    def test_invalid_configs_still_raise_useful_errors(self) -> None:
        cases = [
            ('{"categories":', "Invalid JSON"),
            ("[]", "The configuration root must be a JSON object"),
            ('{"categories": "wrong"}', "'categories' must be a list"),
        ]

        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-8", "utf-8-sig"):
                for content, message in cases:
                    with self.subTest(encoding=encoding, content=content):
                        path = Path(directory) / "config.json"
                        path.write_text(content, encoding=encoding)

                        with self.assertRaises(CategoryConfigError) as caught:
                            load_categorizer(path)

                        self.assertIn(message, str(caught.exception))

    def test_utf8_encodings_preserve_non_ascii_content(self) -> None:
        payload = {
            "default_category": "其他",
            "categories": [
                {
                    "name": "学习",
                    "color": "#111111",
                    "keywords": ["论文", "编程"],
                }
            ],
        }
        results = []

        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-8", "utf-8-sig"):
                with self.subTest(encoding=encoding):
                    path = Path(directory) / f"{encoding}.json"
                    path.write_text(
                        json.dumps(payload, ensure_ascii=False),
                        encoding=encoding,
                    )
                    categorizer = load_categorizer(path)

                    self.assertEqual(categorizer.default_name, "其他")
                    self.assertEqual(categorizer.categories[0].name, "学习")
                    self.assertEqual(
                        categorizer.categories[0].keywords,
                        ("论文", "编程"),
                    )
                    self.assertEqual(
                        categorizer.categorize("editor", "阅读论文"),
                        ("学习", "#111111"),
                    )
                    results.append(categorizer)

        self.assertEqual(results[0].categories, results[1].categories)
        self.assertEqual(results[0].default_name, results[1].default_name)
        self.assertEqual(results[0].default_color, results[1].default_color)

    def test_utf8_bom_configuration_loads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"categories": []}', encoding="utf-8-sig")
            categorizer = load_categorizer(path)

        self.assertEqual(categorizer.categories, [])
    def test_first_case_insensitive_keyword_wins(self) -> None:
        payload = {
            "default_category": "Other",
            "categories": [
                {"name": "Work", "color": "#111111", "keywords": ["GitHub"]},
                {"name": "Leisure", "color": "#222222", "keywords": ["Firefox"]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            categorizer = load_categorizer(path)

        self.assertEqual(
            categorizer.categorize("firefox.exe", "Pull request · github.com"),
            ("Work", "#111111"),
        )
        self.assertEqual(
            categorizer.categorize("unknown.exe", "No match"),
            ("Other", "#64748b"),
        )
        self.assertEqual(
            categorizer.categorize("code.exe", "Project", is_idle=True),
            ("Idle", "#94a3b8"),
        )

    def test_invalid_category_list_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"categories": "non"}', encoding="utf-8")
            with self.assertRaises(CategoryConfigError):
                load_categorizer(path)


if __name__ == "__main__":
    unittest.main()
