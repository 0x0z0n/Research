#!/bin/bash

service postgresql start

echo "Waiting for PostgreSQL to start..."
for i in {1..10}; do
    if pg_isready -q; then
        echo "PostgreSQL is ready."
        break
    fi
    sleep 1
done

if ! pg_isready -q; then
    echo "PostgreSQL failed to start."
    exit 1
fi

export CTF_DB_PASSWORD=$(openssl rand -base64 32)
if [ -z "$CTF_DB_PASSWORD" ]; then
    echo "Failed to generate database password!"
    exit 1
fi
echo "Dynamic database password generated."

sudo -u postgres psql -c "CREATE USER ctf_user WITH PASSWORD '$CTF_DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE ctf_db OWNER ctf_user;"

echo "Database 'ctf_db' and user 'ctf_user' created."

echo "Starting CTF web server on :8080..."
./ctf-server