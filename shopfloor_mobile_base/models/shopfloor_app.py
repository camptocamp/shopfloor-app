# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, tools

from odoo.addons.shopfloor_base.utils import get_version

from .. import importmap


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    js_version_mode = fields.Selection(
        selection=[
            ("module", "Module version"),
            ("file", "File content"),
        ],
        string="JS version mode",
        default="module",
        required=True,
        help="Version appended to the URL of the app's static files "
        "to bust browser cache.\n"
        "* Module version: the version of the Odoo module providing the file. "
        "Fast, but files are refreshed only when the module version changes.\n"
        "* File content: a hash of the content of each file. "
        "Files are refreshed as soon as they change, "
        "but each file is read once per worker.",
    )

    @api.model
    @tools.ormcache()
    def _get_app_js_module_names(self):
        """Return the names of the modules providing JS files to the app.

        These are `shopfloor_mobile_base` and all the installed modules
        depending on it, directly or indirectly.
        """
        base = (
            self.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "shopfloor_mobile_base")])
        )
        return tuple(sorted((base | base.downstream_dependencies()).mapped("name")))

    @api.model
    def _get_app_js_file_list(self):
        """Return `(url, filepath)` for every JS file the app can import.

        The list is computed once per process (files change only on deploy),
        except in dev mode where new files must be picked up right away.
        """
        if tools.config.get("dev_mode"):
            return self._collect_app_js_files()
        return self._get_app_js_file_list_cached()

    @api.model
    @tools.ormcache()
    def _get_app_js_file_list_cached(self):
        return self._collect_app_js_files()

    @api.model
    def _collect_app_js_files(self):
        res = []
        for module_name in self._get_app_js_module_names():
            res.extend(importmap.module_js_files(module_name))
        return tuple(res)

    def _get_app_js_module_version(self, module_name):
        """Return the version used for the static files of given module.

        Override to use your own versioning policy (eg: project version).
        """
        return get_version(module_name)

    def _get_app_static_url(self, url, filepath=None):
        """Return given static URL with a version, according to `js_version_mode`.

        URLs that are not static URLs (`/module/static/...`) are returned
        untouched, as well as URLs of missing files in `file` mode.
        """
        if self.js_version_mode == "file":
            return importmap.versioned_url(url, filepath)
        module_name = importmap.url_module_name(url)
        if not module_name:
            return url
        return f"{url}?v={self._get_app_js_module_version(module_name)}"

    def _get_app_js_files(self):
        """Return `{url: versioned_url}` for every JS file the app can import."""
        return {
            url: self._get_app_static_url(url, filepath)
            for url, filepath in self._get_app_js_file_list()
        }

    def _get_app_js_overrides(self):
        """Return the JS modules to replace in the app.

        Override this method to replace a JS module of the app with your own.
        Every `import` of the original module, from any module,
        loads the replacement instead.

        The replacement can import the original URL to extend it,
        and it must export the same names, eg:

            def _get_app_js_overrides(self):
                res = super()._get_app_js_overrides()
                res.append(
                    (
                        "/shopfloor_mobile_base/static/src/services/process_registry.esm.js",
                        "/my_module/static/src/services/process_registry.esm.js",
                    )
                )
                return res

        Always append to the result of `super()`: when several modules
        replace the same URL, each replacement gets the previous one
        when importing the original URL.

        :return: list of `(original_url, replacement_url)` tuples.
        """
        return []

    def _make_app_importmap(self):
        """Return the import map of the app, ready to be dumped as JSON."""
        return importmap.build_importmap(
            self._get_app_js_files(),
            self._get_app_js_overrides(),
            versioner=self._get_app_static_url,
        )
