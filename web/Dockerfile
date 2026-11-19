# Web page: Next.js "standalone" output, a small self-contained Node server.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# next.config.ts is read during `next build`: the /api rewrite target is fixed here.
ARG API_URL=http://api:8000
ENV API_URL=$API_URL \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build
# Image optimisation is off (next.config.ts): leave out sharp and its LGPL-3.0 libvips binary (27 MB).
# Removed here, before the copy below: deleting it in a later layer would not make the image smaller.
RUN cd .next/standalone/node_modules && rm -rf sharp @img @emnapi

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /app/.next/standalone ./
COPY --from=build --chown=app:app /app/.next/static ./.next/static
USER app
EXPOSE 3000
CMD ["node", "server.js"]
