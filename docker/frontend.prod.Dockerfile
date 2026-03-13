FROM node:20-alpine AS builder

WORKDIR /usr/src/frontend
COPY frontend-solid/package*.json ./
RUN npm ci
COPY frontend-solid/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY docker/frontend.prod.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /usr/src/frontend/dist /usr/share/nginx/html

EXPOSE 80
