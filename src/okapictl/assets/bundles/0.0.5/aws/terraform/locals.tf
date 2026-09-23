locals {
  tags = {
    Project = var.project_name
  }

  ssm_prefix = "/${var.project_name}"

  okapi_tags = merge(local.tags, {
    Name              = "${var.project_name}-okapi"
    Role              = "okapi-stack"
    OkapiDeployTarget = "okapi-stack"
  })

  otel_tags = merge(local.tags, {
    Name              = "${var.project_name}-otel"
    Role              = "otel-demo"
    OkapiDeployTarget = "otel-demo"
  })
}
