#!/bin/sh

docker build -t f24-backend ./backend
docker build -t f24-frontend ./frontend

docker network create f24-net 2>/dev/null

docker rm -f f24-backend 2>/dev/null
docker rm -f f24-frontend 2>/dev/null

docker run -d \
  --name f24-backend \
  --network f24-net \
  -p 8000:8000 \
  -v ./backend:/usr/src/app:Z \
  f24-backend:latest

docker run -d \
  --name f24-frontend \
  --network f24-net \
  -p 4173:4173 \
  -e BACKEND_URL=http://f24-backend:8000 \
  f24-frontend:latest
