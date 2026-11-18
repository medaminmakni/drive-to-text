// Shared by the server layout (inline script) and the client Welcome component.
// Kept out of Welcome.tsx because values exported from a "use client" file are not plain values on the server.

/** Key in sessionStorage: the animation plays once per browser session. */
export const WELCOME_KEY = "dtt-welcome-seen";

/**
 * Runs in <head> before the first paint (see app/layout.tsx). If the animation was already
 * shown in this session, or the user asked the system to reduce motion, it marks <html>
 * so the CSS hides the overlay at once: no flash on reload.
 */
export const WELCOME_SCRIPT = `(function(){try{if(sessionStorage.getItem("${WELCOME_KEY}")||matchMedia("(prefers-reduced-motion: reduce)").matches)document.documentElement.setAttribute("data-welcome","seen")}catch(e){}})()`;
