locals {
  allowed_emails_js = jsonencode(var.allowed_emails)
}

resource "auth0_action" "email_allowlist" {
  name    = "email-allowlist"
  runtime = "node22"
  deploy  = true
  supported_triggers {
    id      = "post-login"
    version = "v3"
  }
  code = <<-EOT
    /**
     * Post-login Action: allow only configured email addresses.
     */
    exports.onExecutePostLogin = async (event, api) => {
      const allowed = ${local.allowed_emails_js};
      const email = (event.user && event.user.email || '').toLowerCase();
      if (!email || !allowed.map(e => e.toLowerCase()).includes(email)) {
        api.access.deny('access_denied', 'This application is restricted to authorized users.');
      }
    };
  EOT
}
