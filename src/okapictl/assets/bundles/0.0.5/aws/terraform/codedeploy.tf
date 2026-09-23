resource "aws_s3_bucket" "artifacts" {
  bucket_prefix = "${var.project_name}-codedeploy-"
  force_destroy = true

  tags = local.tags
}

resource "aws_iam_policy" "instance_artifacts" {
  name = "${var.project_name}-instance-artifacts"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.artifacts.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "instance_artifacts" {
  role       = aws_iam_role.instance.name
  policy_arn = aws_iam_policy.instance_artifacts.arn
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_codedeploy_app" "okapi" {
  compute_platform = "Server"
  name             = "${var.project_name}-okapi-stack"

  tags = local.tags
}

resource "aws_codedeploy_app" "otel" {
  compute_platform = "Server"
  name             = "${var.project_name}-otel-demo"

  tags = local.tags
}

resource "aws_codedeploy_deployment_group" "okapi" {
  app_name              = aws_codedeploy_app.okapi.name
  deployment_group_name = "${var.project_name}-okapi-stack"
  service_role_arn      = aws_iam_role.codedeploy.arn

  ec2_tag_set {
    ec2_tag_filter {
      key   = "OkapiDeployTarget"
      type  = "KEY_AND_VALUE"
      value = "okapi-stack"
    }
  }

  deployment_config_name = "CodeDeployDefault.OneAtATime"

  tags = local.tags
}

resource "aws_codedeploy_deployment_group" "otel" {
  app_name              = aws_codedeploy_app.otel.name
  deployment_group_name = "${var.project_name}-otel-demo"
  service_role_arn      = aws_iam_role.codedeploy.arn

  ec2_tag_set {
    ec2_tag_filter {
      key   = "OkapiDeployTarget"
      type  = "KEY_AND_VALUE"
      value = "otel-demo"
    }
  }

  deployment_config_name = "CodeDeployDefault.OneAtATime"

  tags = local.tags
}
