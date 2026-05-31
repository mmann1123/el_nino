#!/bin/sh
# Substitute country URLs into index.html at container startup. Runs from
# /docker-entrypoint.d/ alphabetically after nginx's 20-envsubst-on-templates,
# so by the time we run, /etc/nginx/conf.d/default.conf is already correct
# and we only need to fix the HTML.
set -e

sed \
  -e "s|__ES_URL__|${ES_URL}|g" \
  -e "s|__HT_URL__|${HT_URL}|g" \
  /usr/share/nginx/html/index.html.template \
  > /usr/share/nginx/html/index.html

echo "Landing: substituted ES_URL=${ES_URL} HT_URL=${HT_URL} into index.html"
