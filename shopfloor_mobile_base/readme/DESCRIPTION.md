Base frontend for Shopfloor applications.

The work is organized in scenario. A scenario represents a process in
the workplace (eg: for WMS -\> receive, deliver). The app allows to
start each process through the main menu.

Each scenario is linked to a specific menu item which can be configured
in the backend. Each scenario drives you through the work to do.

## Tech details

- This frontend is built on top of [VueJS](vuejs.org) and
  [VuetifyJS](vuetifyjs.com/) and relies on shopfloor module that
  exposes REST API in Odoo (based in turn on
  [base_rest](https://github.com/OCA/rest-framework/tree/13.0/base_rest)).

- The whole business logic comes from shopfloor_base module, this module
  takes care of providing a nice and reactive UI to work with.

- No Odoo JS is used, no assets machinery used.

  Static assets are plain ES modules served straight from each module's
  `static` folder. This app is a Single Page App, hence resources are
  loaded only once.

  An [import map](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script/type/importmap)
  generated server side appends a version (module version or content
  hash) to the URL of each JS file, so that a file is downloaded again
  only when it changes. The same map allows to replace any JS module with
  your own. See "Assets" in the usage section.

- When developing you can use a demo mode which allows to define
  interactive scenario with pure JS demo data, without interacting with
  Odoo. Nothing to deal with Odoo demo data.
