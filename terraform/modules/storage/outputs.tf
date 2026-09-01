output "bucket_name" {
  value = aws_s3_bucket.images.id
}

output "bucket_domain_name" {
  description = "Public URL base for uploaded images"
  value       = aws_s3_bucket.images.bucket_regional_domain_name
}
