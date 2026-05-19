output "issuer" {
  description = "OIDC issuer URL (JWT iss claim)"
  value       = "https://${var.auth0_domain}/"
}

output "auth0_domain" {
  description = "Auth0 tenant hostname"
  value       = var.auth0_domain
}

output "api_audience" {
  description = "API identifier to use as audience for access tokens"
  value       = auth0_resource_server.web0personal_vector_api.identifier
}

output "spa_client_id" {
  description = "Auth0 SPA application client ID"
  value       = auth0_client.spa.client_id
}
