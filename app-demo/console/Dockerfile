# Stage 1: build the Angular app
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration production

# Stage 2: serve static files with Caddy (Caddyfile is mounted at /etc/caddy/Caddyfile)
FROM caddy:2.10-alpine
COPY --from=build /app/dist/console/browser /srv
