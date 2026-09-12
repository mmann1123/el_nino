#!/bin/sh
# Substitute country URLs into index.html at container startup. Runs from
# /docker-entrypoint.d/ alphabetically after nginx's 20-envsubst-on-templates,
# so by the time we run, /etc/nginx/conf.d/default.conf is already correct
# and we only need to fix the HTML.
set -e

# Google Analytics: kept to one line, and deliberately spelled without `&` or
# `|` — `|` is this sed's delimiter and `&` means "the whole match" in a
# replacement, so the canonical `dataLayer = dataLayer || []` is written as an
# if-guard instead. Empty when GA_MEASUREMENT_ID is unset, so an untagged
# deploy serves the page with no analytics rather than a broken tag.
if [ -n "${GA_MEASUREMENT_ID:-}" ]; then
  GA_SNIPPET="<script async src=\"https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}\"></script><script>if (!window.dataLayer) { window.dataLayer = []; }function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', '${GA_MEASUREMENT_ID}');</script>"
else
  GA_SNIPPET=""
fi

sed \
  -e "s|__ES_URL__|${ES_URL}|g" \
  -e "s|__HT_URL__|${HT_URL}|g" \
  -e "s|__GA_SNIPPET__|${GA_SNIPPET}|g" \
  /usr/share/nginx/html/index.html.template \
  > /usr/share/nginx/html/index.html

echo "Landing: substituted ES_URL=${ES_URL} HT_URL=${HT_URL} into index.html"
echo "Landing: GA_MEASUREMENT_ID=${GA_MEASUREMENT_ID:-<unset>}"
