variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "alert_email" {
  description = "Email to receive CloudWatch alarm notifications"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch metrics"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for CloudWatch metrics"
  type        = string
}

variable "asg_name" {
  description = "Auto Scaling Group name"
  type        = string
}

variable "db_instance_id" {
  description = "RDS instance identifier"
  type        = string
}
