FROM node:24.21.0-slim AS build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

COPY frontend/ .
RUN npm run build

FROM nginx:1.30.5

RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/nginx/http.conf deploy/nginx/https.conf /etc/nginx/available/
COPY deploy/nginx/snippets/ /etc/nginx/snippets/
COPY deploy/entrypoint.sh /entrypoint.sh
COPY --from=build /frontend/dist /usr/share/nginx/html

ENTRYPOINT ["/entrypoint.sh"]
