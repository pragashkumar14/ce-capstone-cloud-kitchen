provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ce-capstone-cloud-kitchen"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = var.availability_zones
}
module "compute" {
  source = "./modules/compute"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  public_subnet_ids      = module.networking.public_subnet_ids
  db_secret_arn          = module.database.db_secret_arn
  private_app_subnet_ids = module.networking.private_app_subnet_ids
}

module "database" {
  source = "./modules/database"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_db_subnet_ids = module.networking.private_db_subnet_ids
  app_security_group_id = module.compute.app_security_group_id
}
