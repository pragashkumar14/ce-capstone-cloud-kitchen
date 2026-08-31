output "alb_dns_name" {
  description = "Public DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  value = aws_lb.main.arn
}

output "alb_zone_id" {
  description = "Needed later for Route53 alias record"
  value       = aws_lb.main.zone_id
}

output "app_security_group_id" {
  value = aws_security_group.app.id
}

output "asg_name" {
  value = aws_autoscaling_group.app.name
}

output "route53_nameservers" {
  description = "Nameservers to configure at your domain registrar (Namecheap)"
  value       = aws_route53_zone.main.name_servers
}

output "route53_nameservers" {
  description = "Nameservers to configure at your domain registrar (Namecheap)"
  value       = aws_route53_zone.main.name_servers
}
