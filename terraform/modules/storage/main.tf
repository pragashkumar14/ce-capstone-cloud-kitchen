resource "aws_s3_bucket" "images" {
  bucket_prefix = "${var.project_name}-${var.environment}-images-"
}

# S3 blocks public access by default; we selectively allow it
# ONLY via bucket policy (not ACLs), and only for the images/ prefix.
resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "images_public_read" {
  bucket     = aws_s3_bucket.images.id
  depends_on = [aws_s3_bucket_public_access_block.images]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadImagesOnly"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.images.arn}/images/*"
    }]
  })
}
