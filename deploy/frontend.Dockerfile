FROM node:24.21.0-slim AS build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

COPY frontend/ .
RUN npm run build && npm prune --omit=dev --no-audit --no-fund

FROM node:24.21.0-slim AS site

ENV NODE_ENV=production HOST=0.0.0.0 PORT=4321
WORKDIR /site
COPY --from=build /frontend/package.json ./
COPY --from=build /frontend/node_modules ./node_modules
COPY --from=build /frontend/dist ./dist
USER node
EXPOSE 4321
CMD ["node", "dist/server/entry.mjs"]

FROM nginx:1.30.5 AS web

RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/nginx/http.conf deploy/nginx/https.conf /etc/nginx/available/
COPY deploy/nginx/snippets/ /etc/nginx/snippets/
COPY deploy/entrypoint.sh /entrypoint.sh
COPY --from=build /frontend/dist/client /usr/share/nginx/html

ENTRYPOINT ["/entrypoint.sh"]
