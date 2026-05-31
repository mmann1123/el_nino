# Tiny nginx-based static server for the country-picker landing page.
# Build context: the el_nino/ project root (so it can see both ./landing/
# and ./static/).
#
# At container startup:
#   1. nginx's built-in entrypoint runs envsubst on
#      /etc/nginx/templates/*.template → /etc/nginx/conf.d/*  (substitutes
#      ${PORT})
#   2. Our 40-substitute-urls.sh runs sed on index.html.template,
#      replacing __ES_URL__ / __HT_URL__ with the values from env vars,
#      writing the final index.html.
#   3. nginx starts and serves the result.

FROM nginx:1.27-alpine

# Static assets referenced by index.html (video bg + GW logo)
COPY static/ /usr/share/nginx/html/static/

# index.html — kept as a template; URLs substituted at container startup
COPY landing/index.html /usr/share/nginx/html/index.html.template

# nginx config — listens on ${PORT}, which Cloud Run injects
COPY landing/nginx.conf.template /etc/nginx/templates/default.conf.template

# URL-substitution entrypoint (runs after the envsubst on conf templates)
COPY landing/entrypoint.sh /docker-entrypoint.d/40-substitute-urls.sh
RUN chmod +x /docker-entrypoint.d/40-substitute-urls.sh

# Cloud Run sets $PORT; fall back to 8080 for local testing
ENV PORT=8080

# Country URLs — set at deploy time via Cloud Run env vars
ENV ES_URL="#"
ENV HT_URL="#"
