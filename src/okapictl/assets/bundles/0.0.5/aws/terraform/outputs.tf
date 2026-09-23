output "aws_region" {
  value = var.aws_region
}

output "route53_zone_id" {
  value = var.route53_zone_id
}

output "okapi_instance_id" {
  value = aws_instance.okapi.id
}

output "otel_instance_id" {
  value = aws_instance.otel.id
}

output "okapi_public_ip" {
  value = aws_eip.okapi.public_ip
}

output "otel_public_ip" {
  value = aws_eip.otel.public_ip
}

output "okapi_url" {
  value = "https://${var.okapi_hostname}"
}

output "otel_url" {
  value = "https://${var.otel_hostname}"
}

output "codedeploy_artifact_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "okapi_codedeploy_app" {
  value = aws_codedeploy_app.okapi.name
}

output "okapi_codedeploy_group" {
  value = aws_codedeploy_deployment_group.okapi.deployment_group_name
}

output "otel_codedeploy_app" {
  value = aws_codedeploy_app.otel.name
}

output "otel_codedeploy_group" {
  value = aws_codedeploy_deployment_group.otel.deployment_group_name
}

output "ssm_prefix" {
  value = local.ssm_prefix
}
