# Google social login is NOT managed by default — use an existing tenant connection.
# Set manage_google_connection = true (and google_client_id/secret) only for greenfield tenants.

resource "auth0_connection" "google" {
  count    = var.manage_google_connection ? 1 : 0
  name     = "google-oauth2"
  strategy = "google-oauth2"

  options {
    client_id                = var.google_client_id
    client_secret            = var.google_client_secret
    scopes                   = ["email", "profile"]
    set_user_root_attributes = "on_each_login"
  }
}

resource "auth0_connection_clients" "google_spa" {
  count         = var.manage_google_connection ? 1 : 0
  connection_id = auth0_connection.google[0].id
  enabled_clients = [
    auth0_client.spa.id,
  ]
}
