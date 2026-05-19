resource "auth0_resource_server" "web0personal_vector_api" {
  name                                            = var.api_name
  identifier                                      = var.api_identifier
  signing_alg                                     = "RS256"
  token_lifetime                                  = 86400
  allow_offline_access                            = true
  skip_consent_for_verifiable_first_party_clients = true
}
