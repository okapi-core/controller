resource "aws_route53_record" "okapi" {
  zone_id = var.route53_zone_id
  name    = "${trimsuffix(var.okapi_hostname, ".")}."
  type    = "A"
  ttl     = 60
  records = [aws_eip.okapi.public_ip]
}

resource "aws_route53_record" "otel" {
  zone_id = var.route53_zone_id
  name    = "${trimsuffix(var.otel_hostname, ".")}."
  type    = "A"
  ttl     = 60
  records = [aws_eip.otel.public_ip]
}
