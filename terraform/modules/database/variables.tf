variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_db_subnet_ids" {
  description = "Private DB-tier subnet IDs"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group ID of the app tier — only source allowed to reach RDS"
  type        = string
}

variable "db_name" {
  type    = string
  default = "cloudkitchen"
}

variable "db_username" {
  type    = string
  default = "ckadmin"
}

variable "instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}
