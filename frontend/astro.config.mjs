import node from "@astrojs/node";
import { defineConfig, envField } from "astro/config";
import { PRODUCTION, SITE_MODES } from "./src/lib/site-mode";

export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  trailingSlash: "ignore",
  build: {
    inlineStylesheets: "never",
  },
  env: {
    schema: {
      API_URL: envField.string({ context: "server", access: "secret", default: "http://127.0.0.1:8000" }),
      SITE_MODE: envField.enum({ context: "server", access: "secret", values: [...SITE_MODES], default: PRODUCTION }),
    },
  },
  devToolbar: {
    enabled: false,
  },
  server: {
    host: "127.0.0.1",
  },
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
    server: {
      proxy: {
        "/api": "http://127.0.0.1:8000",
        "/admin": "http://127.0.0.1:8000",
        "/static": "http://127.0.0.1:8000",
        "/media": "http://127.0.0.1:8000",
      },
    },
  },
});
