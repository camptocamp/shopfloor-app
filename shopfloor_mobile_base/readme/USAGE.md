## Pre-requisites

- Your Odoo instance is accessible via mobile device
- You have an API Key configured

## Start the app

- Go to "Inventory -\> Configuration -\> Shopfloor -\> Shopfloor App"
- In the login screen fill in your API key
- Hit "Login"

## Select a profile

Several profiles can be configured in the backend, you must choose one
before starting.

- Tap on "Configure profile"
- Select a profile

This will load all available menu items for the selected profile.

## Change language

- Go to "Settings -\> Language"
- Select a language

## Customization

Please refer to shopfloor_mobile_custom_example.

## Working environment

You can control which running env is considerd by Odoo config or env
vars.

For Odoo config: running_env or shopfloor_running_env.

For env var: RUNNING_ENV or SHOPFLOOR_RUNNING_ENV.

Expected key RUNNING_ENV is compliant w/ server_environment naming but
is not depending on it.

Additionally, as specific key for Shopfloor is supported.

**You don't need \`server_environment\` module to use this feature.**

## Assets

The app does not use Odoo assets bundles: JS and CSS files are served
straight from the `static` folder of each module, and JS modules are
loaded via the import map provided by `app_shell_core` (see its readme
for how it works, versioning, overrides and browser support).

`shopfloor.app` inherits `app.shell.mixin.importmap`, with `shopfloor_mobile_base`
as root module (`get_app_js_root_modules`): the import map covers the JS
files of
`shopfloor_mobile_base` and of all the installed modules depending on it.
The main template (`shopfloor_mobile_base.shopfloor_app_main`) renders it
before any other script.

The JS version mode (`js_version_mode`) is visible in debug mode on the
app form. With the default "Module version" mode, remember to bump the
version of your modules when their JS changes. While developing, use
`?debug=assets`: Odoo then serves static files without cache.

## Assets: loading your files

Add your files by inheriting `shopfloor_mobile_base.shopfloor_app_assets`
(or `shopfloor_mobile_base.shopfloor_app_demo_assets` for demo data).

ES modules must be loaded with an inline module importing the plain URL:

``` xml
<t id="new_scenario_hook" position="before">
    <script id="script_scenario_my_scenario" type="module">
        import "/my_module/static/src/scenario/my_scenario.esm.js";
    </script>
</t>
```

Do not use `src` for ES modules: the import map does not apply to the
`src` attribute, the file would be loaded twice (once via `src`, once
via the map when imported by another module) and it would not be
versioned. Files that are only imported by other files (registries,
services, mixins, ...) do not need a tag at all.

Classic scripts and stylesheets cannot use the import map: use the
`static_url` helper to get a versioned URL:

``` xml
<link
    id="link_css_my_module"
    t-att-href="static_url('/my_module/static/src/css/main.css')"
    rel="stylesheet"
/>
```

Tags are executed in the order they appear in the template, keep the
`id` attribute on them so that other modules can hook to them.

## Assets: replacing a JS module

Replacing the tag of a module in the template does not replace the
module: other modules keep importing the original URL. To replace a
module everywhere, override `shopfloor.app.get_app_js_overrides`:

``` python
class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    def get_app_js_overrides(self):
        res = super().get_app_js_overrides()
        res.append(
            (
                "/shopfloor_mobile_base/static/src/services/process_registry.esm.js",
                "/my_module/static/src/services/process_registry.esm.js",
            )
        )
        return res
```

Every import of the original URL now loads your file. Inside your file,
the original URL still points to the original module, so you can extend
it (see `app_shell_core`). Your module must export the same names:

``` javascript
import {ProcessRegistry} from "/shopfloor_mobile_base/static/src/services/process_registry.esm.js";

export class MyProcessRegistry extends ProcessRegistry {
    // ...
}

export var process_registry = new MyProcessRegistry();
// Allow further overrides to extend this one
export {MyProcessRegistry as ProcessRegistry};
```

Several modules can replace the same file: always append to the result
of `super()`. The method is called on the app record: you can return
different overrides per app (eg: based on `self.tech_name`).
