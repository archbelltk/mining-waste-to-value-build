# postgis/postgis ships PostGIS but not pgvector; it's built on postgres:16 with
# the PGDG apt repo already configured, so pgvector installs as a plain package.
FROM postgis/postgis:16-3.4

# -o Acquire::Check-Valid-Until=false: the postgis/postgis base image's Debian
# security-repo release metadata goes stale between image builds; this just
# skips the staleness check, it doesn't disable signature verification.
RUN apt-get update -o Acquire::Check-Valid-Until=false \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
