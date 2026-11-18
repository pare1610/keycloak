# Prueba el cliente service-account mcp-admin (client_credentials) sin mostrar el secreto ni el token.
# Lee el secreto de SecretStore (KeycloakMcpClientSecret).
$secret = Get-Secret -Name KeycloakMcpClientSecret -AsPlainText
$base = 'https://erp.proelectricos.com/auth'
try {
    $r = Invoke-RestMethod -Method Post -Uri "$base/realms/MDSERP/protocol/openid-connect/token" `
        -Body @{ grant_type = 'client_credentials'; client_id = 'mcp-admin'; client_secret = $secret } -TimeoutSec 20
    $p = $r.access_token.Split('.')[1].Replace('-', '+').Replace('_', '/'); while ($p.Length % 4) { $p += '=' }
    $c = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p)) | ConvertFrom-Json
    "Token OK (expira en $($r.expires_in)s), usuario: $($c.preferred_username)"
    "Roles de realm: $($c.realm_access.roles -join ', ')"
    $c.resource_access.PSObject.Properties | ForEach-Object { "Roles de $($_.Name): $($_.Value.roles -join ', ')" }
    try {
        $n = Invoke-RestMethod "$base/admin/realms/MDSERP/users/count" -Headers @{ Authorization = "Bearer $($r.access_token)" }
        "API admin OK: $n usuarios en MDSERP"
    } catch { "API admin fallo: $($_.Exception.Message)" }
} catch {
    "Fallo al pedir el token: $($_.Exception.Message) $($_.ErrorDetails.Message)"
} finally {
    Remove-Variable secret, r -ErrorAction SilentlyContinue
}
