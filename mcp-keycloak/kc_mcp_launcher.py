"""
Launcher for the community MCP server `mcp-keycloak` (pinned to 1.2.2).

Why this exists:
  mcp-keycloak 1.2.2 only authenticates with the password grant against the
  `admin-cli` client and ignores CLIENT_ID / CLIENT_SECRET. We want a
  service-account client (client_credentials) instead of a human admin
  password, so this launcher replaces KeycloakClient._get_token before
  starting the server.

Environment:
  SERVER_URL            e.g. https://erp.proelectricos.com  (package appends /auth/...)
  REALM_NAME            realm where the service-account client lives (MDSERP)
  CLIENT_ID             service-account client id (e.g. mcp-admin)
  KC_MCP_CLIENT_SECRET  client secret, injected by start-claude.ps1 from SecretStore

Run:
  uvx --python 3.14 --from mcp-keycloak==1.2.2 --with "mcp[cli]<2" python kc_mcp_launcher.py
  (mcp<2 is required: mcp 2.x removed mcp.server.fastmcp, which 1.2.2 imports.)
"""

import os
import sys

secret = os.environ.get("KC_MCP_CLIENT_SECRET")
if not secret:
    sys.stderr.write(
        "KC_MCP_CLIENT_SECRET is not set. Start Claude with start-claude.ps1 "
        "so the secret is read from SecretStore.\n"
    )
    sys.exit(1)

# The package reads its config at import time, so set it before importing.
os.environ["CLIENT_SECRET"] = secret
# USERNAME is the Windows user name on Windows; make sure it never leaks into
# the package's password-grant path.
os.environ["USERNAME"] = ""
os.environ["PASSWORD"] = ""

from mcp_keycloak.tools import keycloak_client as _kc  # noqa: E402


async def _get_token_client_credentials(self) -> str:
    token_url = (
        f"{self.server_url}/auth/realms/{self.realm_name}"
        "/protocol/openid-connect/token"
    )
    data = {
        "grant_type": "client_credentials",
        "client_id": self.client_id,
        "client_secret": self.client_secret,
    }
    client = await self._ensure_client()
    response = await client.post(token_url, data=data)
    response.raise_for_status()
    self.token = response.json()["access_token"]
    self.refresh_token = None  # client_credentials issues no refresh token
    return self.token


_kc.KeycloakClient._get_token = _get_token_client_credentials

from mcp_keycloak.main import main  # noqa: E402

if __name__ == "__main__":
    main()
