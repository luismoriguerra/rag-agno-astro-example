resource "auth0_resource_server_scope" "api_access" {
  resource_server_identifier = auth0_resource_server.web0personal_vector_api.identifier
  scope                      = "access:api"
  description                = "Access web0personal-vector backend API"
}
