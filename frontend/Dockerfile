# syntax=docker/dockerfile:1

FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=/aitool/api/v1
ARG VITE_BASE_PATH=/aitool
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

RUN npm run build

FROM node:20-alpine AS runtime

WORKDIR /app

COPY package.json package-lock.json vite.config.ts ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

ENV VITE_PREVIEW_API_TARGET=http://api:8000

EXPOSE 4501

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=15s \
  CMD wget -qO- http://127.0.0.1:4501/aitool/ || exit 1

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4501"]
