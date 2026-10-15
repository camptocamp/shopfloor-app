# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class ShopfloorApp(models.Model):
    _name = "shopfloor.app"
    _inherit = ["shopfloor.app", "app.shell.mixin.importmap"]

    def get_app_js_root_modules(self):
        """The app's JS: this module and all the modules depending on it."""
        return ("shopfloor_mobile_base",)
