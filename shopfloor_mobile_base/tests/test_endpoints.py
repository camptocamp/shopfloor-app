# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import re

from odoo.addons.shopfloor_base.tests.common_http import HttpCommonCase
from odoo.addons.shopfloor_base.utils import get_version


class TestEndpointsCase(HttpCommonCase):
    def test_call(self):
        route = self.shopfloor_app.url
        response = self._make_request(route)
        self.assertEqual(response.status_code, 200)

    def test_call_importmap(self):
        response = self._make_request(self.shopfloor_app.url)
        html = response.text
        match = re.search(
            r'<script id="script_importmap" type="importmap">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertTrue(match, "Import map not found")
        importmap = json.loads(match.group(1))
        main_url = "/shopfloor_mobile_base/static/src/main.esm.js"
        self.assertTrue(importmap["imports"][main_url].startswith(main_url + "?v="))
        # The import map must come before any ES module
        self.assertLess(html.index('type="importmap"'), html.index('type="module"'))
        # ES modules are loaded via the import map, not via `src`
        self.assertIn(f'import "{main_url}";', html)
        self.assertNotRegex(html, r'<script[^>]+src="[^"]+\.esm\.js[^"]*"[^>]+module')
        # Classic scripts and styles are versioned too
        version = get_version("shopfloor_mobile_base")
        self.assertIn(
            f'src="/shopfloor_mobile_base/static/src/lib/lodash.min.js?v={version}"',
            html,
        )
        self.assertIn(
            f'href="/shopfloor_mobile_base/static/src/css/main.css?v={version}"', html
        )

    def test_call_importmap_file_mode(self):
        self.shopfloor_app.js_version_mode = "file"
        # Make the value visible to the HTTP request
        self.env.flush_all()
        html = self._make_request(self.shopfloor_app.url).text
        self.assertRegex(
            html, r'src="/shopfloor_mobile_base/static/src/lib/lodash.min.js\?v=\w{12}"'
        )
        self.assertRegex(
            html,
            r'"/shopfloor_mobile_base/static/src/main.esm.js":'
            r' "/shopfloor_mobile_base/static/src/main.esm.js\?v=\w{12}"',
        )
