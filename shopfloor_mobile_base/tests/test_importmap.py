# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import re
import tempfile
from unittest import mock

from odoo.tests.common import TransactionCase

from odoo.addons.shopfloor_base.utils import get_version
from odoo.addons.shopfloor_mobile_base import importmap

MAIN_URL = "/shopfloor_mobile_base/static/src/main.esm.js"
REGISTRY_URL = "/shopfloor_mobile_base/static/src/services/process_registry.esm.js"
# Any existing file of the module will do as replacement
REPLACEMENT_1_URL = "/shopfloor_mobile_base/static/src/services/page_registry.esm.js"
REPLACEMENT_2_URL = "/shopfloor_mobile_base/static/src/services/color_registry.esm.js"
TOKEN_RE = re.compile(r"\?v=[0-9a-f]{12}$")
MODULE_VERSION = "?v=" + get_version("shopfloor_mobile_base")


class TestImportmapTools(TransactionCase):
    def test_file_token(self):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fd:
            fd.write("export const a = 1;")
        self.addCleanup(os.unlink, fd.name)
        token = importmap.file_token(fd.name)
        self.assertEqual(len(token), 12)
        self.assertEqual(importmap.file_token(fd.name), token)
        with open(fd.name, "w") as fd2:
            fd2.write("export const a = 2; // changed")
        self.assertNotEqual(importmap.file_token(fd.name), token)

    def test_versioned_url(self):
        self.assertRegex(importmap.versioned_url(MAIN_URL), TOKEN_RE)
        # Not existing file, not a static URL, path traversal: untouched
        for url in (
            "/shopfloor_mobile_base/static/src/nope.esm.js",
            "/web/login",
            "/shopfloor_mobile_base/static/../__manifest__.py",
        ):
            self.assertEqual(importmap.versioned_url(url), url)

    def test_module_js_files(self):
        urls = dict(importmap.module_js_files("shopfloor_mobile_base"))
        self.assertIn(MAIN_URL, urls)
        self.assertIn(
            "/shopfloor_mobile_base/static/src/lib/vue-super-call.min.js", urls
        )
        for url in urls:
            self.assertTrue(url.endswith((".js", ".mjs")), url)
            self.assertNotIn("/static/description/", url)
        self.assertEqual(list(importmap.module_js_files("not_a_module")), [])

    def test_build_importmap_no_override(self):
        imports = {MAIN_URL: MAIN_URL + "?v=1"}
        self.assertEqual(importmap.build_importmap(imports), {"imports": imports})

    def test_build_importmap_override(self):
        imports = {
            REGISTRY_URL: REGISTRY_URL + "?v=1",
            REPLACEMENT_1_URL: REPLACEMENT_1_URL + "?v=2",
        }
        res = importmap.build_importmap(imports, [(REGISTRY_URL, REPLACEMENT_1_URL)])
        # Everybody gets the replacement
        self.assertEqual(res["imports"][REGISTRY_URL], REPLACEMENT_1_URL + "?v=2")
        # The replacement gets the original
        self.assertEqual(
            res["scopes"],
            {REPLACEMENT_1_URL + "?v=2": {REGISTRY_URL: REGISTRY_URL + "?v=1"}},
        )
        # Input not modified
        self.assertEqual(imports[REGISTRY_URL], REGISTRY_URL + "?v=1")

    def test_build_importmap_override_chain(self):
        imports = {
            REGISTRY_URL: REGISTRY_URL + "?v=1",
            REPLACEMENT_1_URL: REPLACEMENT_1_URL + "?v=2",
            REPLACEMENT_2_URL: REPLACEMENT_2_URL + "?v=3",
        }
        res = importmap.build_importmap(
            imports,
            [(REGISTRY_URL, REPLACEMENT_1_URL), (REGISTRY_URL, REPLACEMENT_2_URL)],
        )
        # Everybody gets the last replacement
        self.assertEqual(res["imports"][REGISTRY_URL], REPLACEMENT_2_URL + "?v=3")
        self.assertEqual(
            res["scopes"],
            {
                # The 1st replacement gets the original
                REPLACEMENT_1_URL + "?v=2": {REGISTRY_URL: REGISTRY_URL + "?v=1"},
                # The 2nd replacement gets the 1st one
                REPLACEMENT_2_URL + "?v=3": {REGISTRY_URL: REPLACEMENT_1_URL + "?v=2"},
            },
        )

    def test_build_importmap_override_not_mapped(self):
        # The replacement is not part of the map (eg: module not depending
        # on shopfloor_mobile_base): it gets versioned anyway.
        res = importmap.build_importmap({}, [(REGISTRY_URL, REPLACEMENT_1_URL)])
        self.assertRegex(res["imports"][REGISTRY_URL], TOKEN_RE)
        self.assertEqual(
            res["imports"][REPLACEMENT_1_URL], res["imports"][REGISTRY_URL]
        )


class TestAppImportmap(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shopfloor_app = cls.env["shopfloor.app"].create(
            {
                "tech_name": "importmap_test",
                "name": "Importmap Test",
                "short_name": "Importmap test",
            }
        )

    def test_module_names(self):
        names = self.shopfloor_app._get_app_js_module_names()
        self.assertIn("shopfloor_mobile_base", names)
        # Modules not depending on shopfloor_mobile_base are not included
        self.assertNotIn("shopfloor_base", names)
        self.assertNotIn("web", names)

    def test_default_mode(self):
        self.assertEqual(self.shopfloor_app.js_version_mode, "module")

    def test_file_list(self):
        urls = dict(self.shopfloor_app._get_app_js_file_list())
        self.assertIn(MAIN_URL, urls)
        self.assertTrue(urls[MAIN_URL].endswith("main.esm.js"))

    def test_static_url_module_mode(self):
        app = self.shopfloor_app
        self.assertEqual(app._get_app_static_url(MAIN_URL), MAIN_URL + MODULE_VERSION)
        css_url = "/shopfloor_mobile_base/static/src/css/main.css"
        self.assertEqual(app._get_app_static_url(css_url), css_url + MODULE_VERSION)
        self.assertEqual(app._get_app_static_url("/web/login"), "/web/login")

    def test_static_url_file_mode(self):
        app = self.shopfloor_app
        app.js_version_mode = "file"
        self.assertRegex(app._get_app_static_url(MAIN_URL), TOKEN_RE)
        missing_url = "/shopfloor_mobile_base/static/src/nope.esm.js"
        self.assertEqual(app._get_app_static_url(missing_url), missing_url)
        self.assertEqual(app._get_app_static_url("/web/login"), "/web/login")

    def test_importmap_module_mode(self):
        res = self.shopfloor_app._make_app_importmap()
        self.assertNotIn("scopes", res)
        self.assertEqual(res["imports"][MAIN_URL], MAIN_URL + MODULE_VERSION)

    def test_importmap_file_mode(self):
        self.shopfloor_app.js_version_mode = "file"
        res = self.shopfloor_app._make_app_importmap()
        self.assertRegex(res["imports"][MAIN_URL], TOKEN_RE)
        self.assertTrue(res["imports"][MAIN_URL].startswith(MAIN_URL))

    def test_importmap_override(self):
        app_class = type(self.shopfloor_app)
        with mock.patch.object(
            app_class,
            "_get_app_js_overrides",
            return_value=[(REGISTRY_URL, REPLACEMENT_1_URL)],
        ):
            res = self.shopfloor_app._make_app_importmap()
        replacement = res["imports"][REPLACEMENT_1_URL]
        self.assertEqual(replacement, REPLACEMENT_1_URL + MODULE_VERSION)
        self.assertEqual(res["imports"][REGISTRY_URL], replacement)
        self.assertEqual(
            res["scopes"][replacement][REGISTRY_URL], REGISTRY_URL + MODULE_VERSION
        )
