# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo.tools import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Create the new columns of `shopfloor.app` before the module is loaded.

    `shopfloor.app` reads its records in `_register_hook` (REST routes boot):
    make sure the new columns exist as early as possible.
    """
    if not version:
        return
    if not sql.column_exists(cr, "shopfloor_app", "js_version_mode"):
        sql.create_column(cr, "shopfloor_app", "js_version_mode", "varchar")
        cr.execute("UPDATE shopfloor_app SET js_version_mode = 'module'")
        _logger.info("shopfloor_app.js_version_mode created, set to 'module'")
