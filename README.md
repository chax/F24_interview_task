This repository provides a solution to an [interview task for F24](task.md).

Solution is written in two parts, backend and frontend. Backend is written in Python using FastAPI framework. Frontend is writen in React with Vite server.

# Backend

## Installing dependencies and running the App in dev mode

Enter backend dir:
```sh
cd backend
```

Initialize virtual environment:
```sh
python -m venv .venv
source .venv/bin/activate
```

Install needed Python libraries in your virtual environvent:
```sh
pip install -r requirements.txt
```

Start the app in dev mode from your virtual environment:
```sh
fastapi dev
```

API will start on default port 8000
You can test the api and check input and output schemas by opening this url:
http://127.0.0.1:8000/docs

Database is sqlite3 database which keeps data in a single file. On first startup, database file will be automatically created.

# Frontend

## Installing dependencies and starting the App in dev mode

In separate terminal enter frontend dir:
```sh
cd frontend
```

Make sure you have node/npm installed.
At the time this was built, these versions were used:

```sh
$ npm -v
11.13.0
$ node -v
v24.17.0
```

Install npm dependencies:
```sh
npm i
```

Run React app using Vite server
```sh
npm run dev --host
```

Vite server will start on default Vite port 5173, so you just open this url in browser:
http://127.0.0.1:5173/

# Vite proxy and CORS for backend API

Frontend App uses Vite proxy to re-route backend API to /api path on the same base url to avoid complications with CORS. This is done just for simplicity sake but in production environment this would be solved in a bit different way. For example both frontend and backend would be deployed separately, maybe even on different machines. Proxy would be deployed separately and configured to route both apps on the same domain/subdomain with different paths. For example, one could use standard NGINX server to achieve this.

# Run solution in Docker/Podman

To run a solution in Docker or Podman, please refer to [this README](README.docker.md)
