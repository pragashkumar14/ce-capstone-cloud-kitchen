output "db_endpoint" {
  description = "RDS connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_secret_arn" {
  description = "Secrets Manager ARN holding the DB credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "db_security_group_id" {
  value = aws_security_group.db.id
}

output "db_address" {
  description = "RDS hostname only, no port"
  value       = aws_db_instance.main.address
}

output "db_instance_id" {
  description = "RDS instance identifier for CloudWatch metrics"
  value       = aws_db_instance.main.id
}
