resource "auth0_client" "spa" {
  name                = var.spa_name
  app_type            = "spa"
  is_first_party      = true
  oidc_conformant     = true
  grant_types         = ["authorization_code", "refresh_token"]
  callbacks           = var.callback_urls
  allowed_logout_urls = var.logout_urls
  web_origins         = var.web_origins
  jwt_configuration {
    lifetime_in_seconds = 36000
  }
}

resource "auth0_client_grant" "spa_api" {
  client_id = auth0_client.spa.id
  audience  = auth0_resource_server.web0personal_vector_api.identifier
  scopes    = [auth0_resource_server_scope.api_access.scope]
}
