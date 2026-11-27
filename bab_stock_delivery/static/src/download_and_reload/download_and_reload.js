import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";

/**
 * Downloads the slips PDF stored in the chatter, then reloads the current
 * view, so the receipt shows "Slips printed" and its new chatter message
 * without a manual refresh (a plain act_url download leaves the form as it was).
 */
function downloadAndReload(env, action) {
    browser.open(action.params.url, "_blank");
    return { type: "ir.actions.client", tag: "soft_reload" };
}

registry.category("actions").add("bab_download_and_reload", downloadAndReload);
