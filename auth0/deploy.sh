#!/bin/bash

# DevSkyy Auth0 Deployment Script
# Enterprise-grade authentication deployment automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AUTH0_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${AUTH0_DIR}/.env"
CONFIG_FILE="${AUTH0_DIR}/config.json"

echo -e "${BLUE}🔐 DevSkyy Auth0 Deployment Script${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if Auth0 Deploy CLI is installed
if ! command -v a0deploy &> /dev/null; then
    echo -e "${RED}❌ Auth0 Deploy CLI not found. Installing...${NC}"
    npm install -g auth0-deploy-cli
fi

# Check for environment file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Environment file not found. Creating template...${NC}"
    cat > "$ENV_FILE" << 'EOF'
# Auth0 Configuration
AUTH0_DOMAIN=devskyy.auth0.com
AUTH0_CLIENT_ID=your-management-api-client-id
AUTH0_CLIENT_SECRET=your-management-api-client-secret
AUTH0_AUDIENCE=https://devskyy.auth0.com/api/v2/

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/devskyy

# Social Provider Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
EOF
    echo -e "${YELLOW}📝 Please update the .env file with your actual credentials${NC}"
    echo -e "${YELLOW}📝 Then run this script again${NC}"
    exit 1
fi

# Load environment variables
source "$ENV_FILE"

# Validate required environment variables
required_vars=("AUTH0_DOMAIN" "AUTH0_CLIENT_ID" "AUTH0_CLIENT_SECRET")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Required environment variable $var is not set${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment variables loaded${NC}"

# Function to replace placeholders in YAML files
replace_placeholders() {
    local file="$1"
    local temp_file="${file}.tmp"
    
    echo -e "${BLUE}🔄 Processing $file...${NC}"
    
    # Replace placeholders with environment variables
    sed "s/@@DATABASE_URL@@/${DATABASE_URL//\//\\/}/g" "$file" > "$temp_file"
    sed -i '' "s/@@GOOGLE_CLIENT_ID@@/${GOOGLE_CLIENT_ID}/g" "$temp_file"
    sed -i '' "s/@@GOOGLE_CLIENT_SECRET@@/${GOOGLE_CLIENT_SECRET}/g" "$temp_file"
    sed -i '' "s/@@APPLE_CLIENT_ID@@/${APPLE_CLIENT_ID}/g" "$temp_file"
    sed -i '' "s/@@APPLE_CLIENT_SECRET@@/${APPLE_CLIENT_SECRET}/g" "$temp_file"
    sed -i '' "s/@@APPLE_TEAM_ID@@/${APPLE_TEAM_ID}/g" "$temp_file"
    sed -i '' "s/@@APPLE_KEY_ID@@/${APPLE_KEY_ID}/g" "$temp_file"
    sed -i '' "s/@@GITHUB_CLIENT_ID@@/${GITHUB_CLIENT_ID}/g" "$temp_file"
    sed -i '' "s/@@GITHUB_CLIENT_SECRET@@/${GITHUB_CLIENT_SECRET}/g" "$temp_file"
    sed -i '' "s/@@LINKEDIN_CLIENT_ID@@/${LINKEDIN_CLIENT_ID}/g" "$temp_file"
    sed -i '' "s/@@LINKEDIN_CLIENT_SECRET@@/${LINKEDIN_CLIENT_SECRET}/g" "$temp_file"
    
    mv "$temp_file" "$file"
}

# Process configuration files
echo -e "${BLUE}🔄 Processing configuration files...${NC}"
replace_placeholders "${AUTH0_DIR}/connections.yaml"

# Backup current configuration (optional)
if [ "$1" = "--backup" ]; then
    echo -e "${BLUE}💾 Creating backup of current Auth0 configuration...${NC}"
    a0deploy export --config_file "$CONFIG_FILE" --output_folder "${AUTH0_DIR}/backup/$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backup created${NC}"
fi

# Deploy to Auth0
echo -e "${BLUE}🚀 Deploying to Auth0...${NC}"

# Set environment variables for deployment
export AUTH0_DOMAIN
export AUTH0_CLIENT_ID
export AUTH0_CLIENT_SECRET
export AUTH0_AUDIENCE

# Deploy configuration
if a0deploy import --config_file "$CONFIG_FILE" --input_file "${AUTH0_DIR}"; then
    echo -e "${GREEN}✅ Auth0 configuration deployed successfully!${NC}"
    echo -e "${GREEN}🎉 DevSkyy authentication system is ready${NC}"
    
    # Display important information
    echo -e "${BLUE}📋 Important Information:${NC}"
    echo -e "${BLUE}========================${NC}"
    echo -e "Auth0 Domain: ${AUTH0_DOMAIN}"
    echo -e "Management API Audience: ${AUTH0_AUDIENCE}"
    echo -e ""
    echo -e "${YELLOW}🔑 Next Steps:${NC}"
    echo -e "1. Update your application environment variables"
    echo -e "2. Configure social provider credentials in Auth0 dashboard"
    echo -e "3. Test authentication flows"
    echo -e "4. Set up custom domain (optional)"
    echo -e ""
    echo -e "${GREEN}🌐 Auth0 Dashboard: https://manage.auth0.com/dashboard/${NC}"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo -e "${RED}Please check the error messages above${NC}"
    exit 1
fi

# Cleanup
echo -e "${BLUE}🧹 Cleaning up temporary files...${NC}"
# Restore original files if needed

echo -e "${GREEN}✅ Deployment complete!${NC}"
