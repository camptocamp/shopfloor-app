# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import re
from unittest import mock

from odoo.tests.common import TransactionCase

from odoo.addons.shopfloor_base.utils import get_version

MAIN_URL = "/shopfloor_mobile_base/static/src/main.esm.js"
REGISTRY_URL = "/shopfloor_mobile_base/static/src/services/process_registry.esm.js"
# Any existing file of the module will do as replacement
REPLACEMENT_1_URL = "/shopfloor_mobile_base/static/src/services/page_registry.esm.js"
TOKEN_RE = re.compile(r"\?v=[0-9a-f]{12}$")
MODULE_VERSION = "?v=" + get_version("shopfloor_mobile_base")


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
        """The app's JS comes from shopfloor_mobile_base and its dependents."""
        names = self.shopfloor_app._get_app_js_module_names()
        self.assertIn("shopfloor_mobile_base", names)
        # Modules not depending on shopfloor_mobile_base are not included
        self.assertNotIn("shopfloor_base", names)
        self.assertNotIn("web", names)

    def test_default_mode(self):
        """Apps use module versions by default."""
        self.assertEqual(self.shopfloor_app.js_version_mode, "module")

    def test_file_list(self):
        """The JS files of shopfloor_mobile_base are listed."""
        urls = dict(self.shopfloor_app._get_app_js_file_list())
        self.assertIn(MAIN_URL, urls)
        self.assertTrue(urls[MAIN_URL].endswith("main.esm.js"))

    def test_static_url_module_mode(self):
        """Static URLs get the module version, others are untouched."""
        app = self.shopfloor_app
        self.assertEqual(app.get_app_static_url(MAIN_URL), MAIN_URL + MODULE_VERSION)
        css_url = "/shopfloor_mobile_base/static/src/css/main.css"
        self.assertEqual(app.get_app_static_url(css_url), css_url + MODULE_VERSION)
        self.assertEqual(app.get_app_static_url("/web/login"), "/web/login")

    def test_static_url_file_mode(self):
        """In file mode, static URLs get a content hash."""
        app = self.shopfloor_app
        app.js_version_mode = "file"
        self.assertRegex(app.get_app_static_url(MAIN_URL), TOKEN_RE)
        missing_url = "/shopfloor_mobile_base/static/src/nope.esm.js"
        self.assertEqual(app.get_app_static_url(missing_url), missing_url)
        self.assertEqual(app.get_app_static_url("/web/login"), "/web/login")

    def test_importmap_module_mode(self):
        """The import map maps files to their module version URL."""
        res = self.shopfloor_app.make_app_importmap()
        self.assertNotIn("scopes", res)
        self.assertEqual(res["imports"][MAIN_URL], MAIN_URL + MODULE_VERSION)

    def test_importmap_file_mode(self):
        """In file mode, the import map maps files to their content hash URL."""
        self.shopfloor_app.js_version_mode = "file"
        res = self.shopfloor_app.make_app_importmap()
        self.assertRegex(res["imports"][MAIN_URL], TOKEN_RE)
        self.assertTrue(res["imports"][MAIN_URL].startswith(MAIN_URL))

    def test_importmap_override(self):
        """Overrides replace the original for everybody, but the replacement."""
        app_class = type(self.shopfloor_app)
        with mock.patch.object(
            app_class,
            "get_app_js_overrides",
            return_value=[(REGISTRY_URL, REPLACEMENT_1_URL)],
        ):
            res = self.shopfloor_app.make_app_importmap()
        replacement = res["imports"][REPLACEMENT_1_URL]
        self.assertEqual(replacement, REPLACEMENT_1_URL + MODULE_VERSION)
        self.assertEqual(res["imports"][REGISTRY_URL], replacement)
        self.assertEqual(
            res["scopes"][replacement][REGISTRY_URL], REGISTRY_URL + MODULE_VERSION
        )

    def test_root_modules(self):
        """shopfloor_mobile_base is the root module of the app's JS."""
        self.assertEqual(
            self.shopfloor_app.get_app_js_root_modules(), ("shopfloor_mobile_base",)
        )
