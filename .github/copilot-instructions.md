# GymSystem MCP

The MCP server is implemented in `mcp_server.py` with the official Python MCP SDK.
It communicates with the FastAPI application over HTTP and preserves the API's JWT authorization.

- MCP SDK documentation: https://modelcontextprotocol.io/docs/sdk
- Python SDK repository: https://github.com/modelcontextprotocol/python-sdk
- Run it with `uv run python mcp_server.py`.
- Configure `MCP_API_URL`, `MCP_ADMIN` (or `MCP_ADMIN_EMAIL`), and `MCP_ADMIN_PASSWORD` in `.env` before using tools.
