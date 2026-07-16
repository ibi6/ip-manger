#!/bin/sh
set -eu

python -m app.db.prepare_database
exec "$@"
