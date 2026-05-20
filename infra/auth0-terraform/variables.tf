variable "auth0_domain" {
  type        = string
  description = "Auth0 tenant domain, e.g. dev-abc.us.auth0.com"
}

variable "auth0_terraform_client_id" {
  type        = string
  description = "Machine-to-machine client ID for Terraform provider"
  sensitive   = true
}

variable "auth0_terraform_client_secret" {
  type        = string
  description = "Client secret for Terraform provider"
  sensitive   = true
}

variable "api_identifier" {
  type        = string
  description = "Identifier (audience) for the web0personal-vector API resource server"
}

variable "api_name" {
  type        = string
  default     = "web0personal-vector API"
  description = "Display name for the Auth0 API"
}

variable "spa_name" {
  type        = string
  default     = "web0personal-vector Web"
  description = "Display name for the SPA application"
}

variable "callback_urls" {
  type        = list(string)
  description = "Allowed callback URLs (include http://localhost:4321/api/auth/callback and production URL)"
}

variable "logout_urls" {
  type        = list(string)
  description = "Allowed logout URLs"
}

variable "web_origins" {
  type        = list(string)
  description = "Allowed web origins (CORS for Auth0-hosted login)"
}

variable "allowed_emails" {
  type        = list(string)
  description = "Email addresses permitted to sign in via post-login Action (set in terraform.tfvars; not committed)"

  validation {
    condition     = length(var.allowed_emails) > 0
    error_message = "allowed_emails must contain at least one email address."
  }
}

variable "manage_google_connection" {
  type        = bool
  default     = false
  description = "Create/manage Google social connection in Terraform. Leave false when Google already exists in the tenant (enable SPA on that connection in the Auth0 dashboard after apply)."
}

variable "google_client_id" {
  type        = string
  description = "Google OAuth client ID — only used when manage_google_connection is true"
  default     = ""
}

variable "google_client_secret" {
  type        = string
  description = "Google OAuth client secret — only used when manage_google_connection is true"
  sensitive   = true
  default     = ""
}
