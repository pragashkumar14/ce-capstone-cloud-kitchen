output "vpc_id" {
  value = module.networking.vpc_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_app_subnet_ids" {
  value = module.networking.private_app_subnet_ids
}

output "private_db_subnet_ids" {
  value = module.networking.private_db_subnet_ids
}
output "alb_dns_name" {
  description = "Public URL of the load balancer (before Route53/ACM)"
  value       = module.compute.alb_dns_name
}

output "db_endpoint" {
  value = module.database.db_endpoint
}

output "db_secret_arn" {
  value = module.database.db_secret_arn
}

output "route53_nameservers" {
  value = module.compute.route53_nameservers
}


output "deploy_bucket_name" {
  value = module.storage.deploy_bucket_name
}
