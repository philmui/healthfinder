# HealthFinder Docker Containerization Tutorial

This guide provides a step-by-step tutorial on how to containerize the HealthFinder application using Docker and Docker Compose. This setup will create a consistent, isolated, and reproducible development environment for both the frontend and backend services.

---

## Table of Contents
1. [Why Use Docker?](#1-why-use-docker)
2. [Prerequisites](#2-prerequisites)
3. [Step 1: Dockerizing the Backend (FastAPI)](#step-1-dockerizing-the-backend-fastapi)
4. [Step 2: Dockerizing the Frontend (Next.js)](#step-2-dockerizing-the-frontend-nextjs)
5. [Step 3: Orchestrating with Docker Compose](#step-3-orchestrating-with-docker-compose)
6. [Step 4: Running the Application](#step-4-running-the-application)
7. [Next Steps](#5-next-steps)

---

### 1. Why Use Docker?

Docker allows us to package our application and its dependencies into a standardized unit called a "container." This has several key benefits:
- **Consistency**: The application runs the same way on your machine, your teammate's machine, and in production.
- **Isolation**: Dependencies for the frontend and backend are kept separate and don't conflict with other projects on your system.
- **Simplicity**: With a single command, you can start up the entire full-stack application.

### 2. Prerequisites

Before you begin, make sure you have **Docker Desktop** installed on your machine. It includes Docker Engine, Docker CLI, and Docker Compose.
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Step 1: Dockerizing the Backend (FastAPI)

First, we'll create a `Dockerfile` for our Python backend. This file contains the instructions to build a Docker image for the service.

Create a file named `Dockerfile` inside the `server/` directory:

**File: `server/Dockerfile`**
```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, our preferred package manager
RUN pip install uv

# Copy the dependency definition files
COPY pyproject.toml ./

# Install project dependencies using uv
# This step is cached by Docker if the dependency files don't change
RUN uv pip install --system -e .[test,dev]

# Copy the rest of the application source code into the container
COPY ./app ./app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Step 2: Dockerizing the Frontend (Next.js)

Next, we'll create a `Dockerfile` for our Next.js frontend. This is very similar to the one outlined in the design document.

Create a file named `Dockerfile` inside the `frontend/` directory:

**File: `frontend/Dockerfile`**
```dockerfile
# Use the official Node.js 18 LTS image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
# Using --frozen-lockfile ensures we use the exact versions from the lockfile
RUN npm install --frozen-lockfile

# Copy the rest of the frontend application code
COPY . .

# The Next.js app will be run in development mode by Docker Compose,
# so we don't need to build it here. The 'npm run dev' command will be used.

# Expose the port Next.js runs on
EXPOSE 3000

# Default command to run the app in development mode
CMD ["npm", "run", "dev"]
```

### Step 3: Orchestrating with Docker Compose

Now that we have `Dockerfile`s for both services, we'll use Docker Compose to define how they run together. Docker Compose reads a `compose.yaml` file to configure and start multiple services.

Create a file named `compose.yaml` in the **root** of your project directory (outside of `frontend/` and `server/`):

**File: `compose.yaml`**
```yaml
version: '3.8'

services:
  # Backend FastAPI Service
  backend:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      # Mount the server code directory into the container for live reloading
      - ./server:/app
    env_file:
      # Load environment variables from the .env file in the server directory
      - ./server/.env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend Next.js Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      # Mount the frontend code directory for live reloading
      - ./frontend:/app
      # Exclude node_modules from being overwritten by the host's empty folder
      - /app/node_modules
    env_file:
      # Load environment variables from the .env.local file
      - ./frontend/.env.local
    depends_on:
      # Wait for the backend service to be ready before starting
      - backend

```

### Step 4: Running the Application

You're all set! Now you can build and run the entire HealthFinder application with a single command.

**1. Prepare Environment Files:**

Make sure you have created your local environment files from the examples:
- Copy `server/.env.example` to `server/.env` and fill in your API keys.
- Copy `frontend/.env.local.example` to `frontend/.env.local` and fill in your OAuth keys. Ensure `NEXT_PUBLIC_API_URL` is set to `http://localhost:8000`.

**2. Start the Services:**

Open your terminal in the root of the HealthFinder project and run:
```bash
docker compose up --build
```
- `--build`: This flag tells Docker Compose to build the images from your `Dockerfile`s before starting the services. You only need to use it the first time or when you change a `Dockerfile` or dependencies.
- `docker compose up`: For subsequent runs, you can just use this command.

**3. Access the Application:**

Once the containers are running, you can access:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

You will see logs from both services interleaved in your terminal. Any changes you make to the source code in `frontend/` or `server/` will automatically trigger a reload inside the respective container.

**4. Stop the Services:**

To stop the application, press `Ctrl + C` in your terminal, and then run:
```bash
docker compose down
```
This command stops and removes the containers, networks, and volumes created by `docker compose up`.

### 5. Next Steps

Congratulations! You now have a fully containerized development environment for HealthFinder. This setup ensures that anyone on the team can get up and running quickly and reliably. From here, you can continue developing features, and the Docker environment will handle the rest.
