resource "auth0_trigger_actions" "post_login_allowlist" {
  trigger = "post-login"

  actions {
    id           = auth0_action.email_allowlist.id
    display_name = auth0_action.email_allowlist.name
  }
}
