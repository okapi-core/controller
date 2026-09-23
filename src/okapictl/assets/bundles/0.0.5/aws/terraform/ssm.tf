resource "aws_ssm_parameter" "config" {
  for_each = {
    "${local.ssm_prefix}/config/aws_region"       = var.aws_region
    "${local.ssm_prefix}/config/okapi_hostname"   = var.okapi_hostname
    "${local.ssm_prefix}/config/otel_hostname"    = var.otel_hostname
    "${local.ssm_prefix}/config/okapi_image_repo" = var.okapi_image_repo
    "${local.ssm_prefix}/config/okapi_image_tag"  = var.okapi_image_tag
  }

  name      = each.key
  type      = "String"
  value     = each.value
  overwrite = true

  tags = local.tags
}

resource "aws_ssm_parameter" "secrets" {
  for_each = {
    "${local.ssm_prefix}/secrets/postgres_password"               = var.postgres_password
    "${local.ssm_prefix}/secrets/okapi_web_db_password"           = var.okapi_web_db_password
    "${local.ssm_prefix}/secrets/okapi_web_migration_db_password" = var.okapi_web_migration_password
    "${local.ssm_prefix}/secrets/oscar_db_password"               = var.oscar_db_password
    "${local.ssm_prefix}/secrets/clickhouse_password"             = var.clickhouse_password
    "${local.ssm_prefix}/secrets/vault_root_token"                = var.vault_root_token
  }

  name      = each.key
  type      = "SecureString"
  value     = each.value
  overwrite = true

  tags = local.tags
}

resource "aws_ssm_parameter" "openai_api_key" {
  count = var.openai_api_key == "" ? 0 : 1

  name      = "${local.ssm_prefix}/secrets/openai_api_key"
  type      = "SecureString"
  value     = var.openai_api_key
  overwrite = true

  tags = local.tags
}
