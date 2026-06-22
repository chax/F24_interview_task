# Using Docker/Podman to run backend App

Make sure you have [Docker installed and set-up](https://docs.docker.com/engine/install/), alternatevly use [Podman](https://podman.io/docs/installation) with docker symlink or alias or directly by just replacing `docker` command with `podman` command. Keep in mind, to run container in [rootless mode](https://github.com/podman-container-tools/podman/blob/main/docs/tutorials/rootless_tutorial.md), add `--userns=keep-id` after `docker run`. If you're using Podman, you can also drop `docker rm -f` command and add `--replace` flag after `docker run` to automatically replace older container instance with new one.

## Build docker image using provided Dockerfile and tag image

Build backend docker image
```sh
docker build -t f24-backend ./backend
```

Build frontend docker image
```sh
docker build -t f24-frontend ./frontend
```

## Run docker image

To make inter-container communication possible, create new docker shared network.

```sh
docker network create f24-net
```

For backend:
 - Bind mount external directory to /usr/src/app so that app can store/read database file.
 - Map internal App port 8000 to external port 8000
 - Use docker network `f24-net`

```sh
docker rm -f f24-backend 2>/dev/null
docker run -d \
  --name f24-backend \
  --network f24-net \
  -p 8000:8000 \
  -v ./backend:/usr/src/app:Z \
  f24-backend:latest
```

For frontend:
 - Map internal App port 4173 to external port 4173
 - Use docker network `f24-net`
 - Provide environment variable BACKEND_URL so that Vite knows where to find API

```sh
docker rm -f f24-frontend 2>/dev/null
docker run -d \
  --name f24-frontend \
  --network f24-net \
  -p 4173:4173 \
  -e BACKEND_URL=http://f24-backend:8000 \
  f24-frontend:latest
```
