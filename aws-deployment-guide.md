# AWS Deployment Guide

## Architecture

```
Internet → CloudFront → S3 (React) + ALB → EC2 (FastAPI) → RDS (PostgreSQL)
```

## Step-by-Step AWS Deployment

### 1. Frontend (React on S3 + CloudFront)

#### Create S3 Bucket

```bash
# Create bucket for static website
aws s3 mb s3://your-hexagon-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://your-hexagon-frontend --index-document index.html --error-document error.html

# Upload React build files
npm run build
aws s3 sync build/ s3://your-hexagon-frontend --delete
```

#### CloudFront Distribution

```json
{
  "DistributionConfig": {
    "CallerReference": "hexagon-frontend",
    "Origins": [
      {
        "Id": "S3-hexagon-frontend",
        "DomainName": "your-hexagon-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ],
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-hexagon-frontend",
      "ViewerProtocolPolicy": "redirect-to-https"
    },
    "Enabled": true
  }
}
```

### 2. Backend (FastAPI on EC2)

#### Launch EC2 Instance

```bash
# Create key pair
aws ec2 create-key-pair --key-name hexagon-key --query 'KeyMaterial' --output text > hexagon-key.pem
chmod 400 hexagon-key.pem

# Launch t2.micro instance (free tier)
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t2.micro \
  --key-name hexagon-key \
  --security-groups hexagon-web
```

#### Setup Script for EC2

```bash
#!/bin/bash
# User data script for EC2 instance

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository
git clone https://github.com/vaengai/hexagon-api.git
cd hexagon-api

# Set environment variables
echo "DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/hexagon" > .env
echo "CLERK_SECRET_KEY=your_clerk_secret" >> .env

# Build and run
docker-compose up -d
```

### 3. Database (RDS PostgreSQL)

#### Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier hexagon-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username hexagon_user \
  --master-user-password your_secure_password \
  --allocated-storage 20 \
  --storage-type gp2 \
  --vpc-security-group-ids sg-xxxxxxxxx
```

## Cost Estimation (Free Tier)

- **EC2 t2.micro**: Free for 12 months (750 hours/month)
- **RDS t3.micro**: Free for 12 months (750 hours/month)
- **S3**: 5GB free storage
- **CloudFront**: 1TB data transfer free
- **Data Transfer**: 100GB free outbound

**Total Cost**: $0 for first 12 months, then ~$15-25/month

## Production Optimizations

- Use Application Load Balancer for high availability
- Enable Auto Scaling Groups
- Use RDS Multi-AZ for database redundancy
- Implement CloudWatch monitoring
