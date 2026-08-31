terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "ce-capstone-cloud-kitchen-tfstate-9c2dbc"
    key            = "terraform.tfstate"
    region         = "eu-west-3"
    encrypt        = true
    dynamodb_table = "ce-capstone-tflock"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
