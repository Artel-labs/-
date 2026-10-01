import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static",
  trailingSlash: "ignore",
  build: {
    format: "directory",
    inlineStylesheets: "never",
  },
  devToolbar: {
    enabled: false,
  },
  server: {
    host: "127.0.0.1",
  },
  vite: {
    server: {
      proxy: {
        "/api": "http://127.0.0.1:8000",
        "/admin": "http://127.0.0.1:8000",
        "/static": "http://127.0.0.1:8000",
      },
    },
  },
});
