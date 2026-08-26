#!/bin/sh
set -e

if [ ! -f configuration/config.json ]; then
    cp configuration/config.example.json configuration/config.json
fi

exec "$@"
