# ============================================
# Dockerfile — Obraz Nginx (Reverse Proxy)
#
# Przygotowano minimalny obraz Nginx z własną konfiguracją.
# ============================================

FROM nginx:1.27-alpine

LABEL maintainer="Jakub Francuz"
LABEL description="TaskFlow Nginx Reverse Proxy"

# Usunięto domyślną konfigurację i zastąpiono własną
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Wyeksponowano port HTTP
EXPOSE 80

# Skonfigurowano health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/nginx-health || exit 1
