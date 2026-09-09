# GYM System

## Local Run
Install dependencies
```bash
pip install uv
```
```bash
uv sync
```
Add `.env` file with the following content:
```yaml
SECRET_KEY=change-me
MONGODB_URI=mongodb://admin:admin123@localhost:27017/?authSource=admin

# TO USE EMAIL
SENDER_EMAIL=youemail@hot.com
SENDER_PASSWORD=your-email-password-for-smtp

# ADMIN EMAIL
ADMIN_EMAIL=example@example.com
```
Add this code to `commons/constants.py`:
```python
from dotenv import load_dotenv

load_dotenv()
```
Run MongoDB database using Docker
```bash
docker compose -f 'docker-compose.yml' up -d --build 'mongodb_gs'
```
Run the API
```bash
cd src
uv run uvicorn app:app --reload --port 8080
```

## Docker Run
Add `.env` file with the following content:
```yaml
SECRET_KEY=change-me
MONGODB_URI=mongodb://admin:admin123@mongodb_gs:27017/?authSource=admin

# TO USE EMAIL
SENDER_EMAIL=youemail@hot.com
SENDER_PASSWORD=your-email-password-for-smtp

# ADMIN EMAIL
ADMIN_EMAIL=example@example.com
```
Run docker compose
```bash
docker compose up --build
```

## API Client
Open the `GymSystemAPI` collection on bruno API Client and use it.
Download Bruno API Client: [Download Bruno API Client](https://www.usebruno.com/downloads)

## MCP Server
The project includes a Python MCP server that exposes GymSystem operations as tools for compatible clients such as VS Code Copilot. Start the API first, then configure the administrator credentials in `.env`:

```bash
MCP_API_URL=http://127.0.0.1:8080
MCP_ADMIN=admin@example.com
MCP_ADMIN_PASSWORD=your-admin-password
```

The MCP server signs in automatically through `POST /admin/sign-in`, caches the JWT in memory,
and refreshes it once if the API returns `401`. In VS Code, the server is already registered
in `.vscode/mcp.json`; starting it there uses the credentials from `.env` without storing a token.
The MCP server preserves the API's role-based authorization, so statistics and write operations
still require the permissions of the configured administrator.

## Tests

Run tests
```bash
uv run pytest
```

## API Documentation

Open the API documentation [here](openapi.json)
