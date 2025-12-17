#!/bin/bash

# DevSkyy Security Hardening Setup Script
# Comprehensive security configuration and hardening

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (not recommended)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create security directories
create_security_dirs() {
    log_info "Creating security directories..."

    directories=(
        "security/ssl"
        "security/keys"
        "security/logs"
        "security/backups"
        "logs"
        "data"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$PROJECT_ROOT/$dir"
        chmod 750 "$PROJECT_ROOT/$dir"
        log_success "Created directory: $dir"
    done
}

# Set secure file permissions
set_file_permissions() {
    log_info "Setting secure file permissions..."

    # Configuration files (600 - owner read/write only)
    config_files=(
        ".env"
        "docker/.env"
        "ml/.env"
        "mcp/.env"
        "pyproject.toml"
        "claude_desktop_config.example.json"
    )

    for file in "${config_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            chmod 600 "$PROJECT_ROOT/$file"
            log_success "Secured $file (600)"
        fi
    done

    # Script files (755 - owner full, group/other read/execute)
    script_files=(
        "setup_compliance.sh"
        "setup_security_hardening.sh"
        "main_enterprise.py"
        "server.py"
    )

    for file in "${script_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            chmod 755 "$PROJECT_ROOT/$file"
            log_success "Secured $file (755)"
        fi
    done

    # Security directories (750 - owner full, group read/execute, other none)
    security_dirs=(
        "security"
        "database"
        "logs"
        "data"
    )

    for dir in "${security_dirs[@]}"; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            chmod 750 "$PROJECT_ROOT/$dir"
            log_success "Secured $dir/ (750)"
        fi
    done
}

# Generate secure environment files
generate_env_files() {
    log_info "Generating secure environment files..."

    # Generate secure keys
    SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
    JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
    ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n')

    # Create main .env file if it doesn't exist
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        cat > "$PROJECT_ROOT/.env" << EOF
# DevSkyy Environment Configuration
# Generated on $(date)

# Core Application
ENVIRONMENT=$ENVIRONMENT
DEBUG=false
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Database
DATABASE_URL=postgresql://devskyy:change-this-password@localhost:5432/devskyy

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services (Add your API keys)
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# WordPress Integration
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your-wp-username
WORDPRESS_PASSWORD=your-wp-app-password

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
EOF
        chmod 600 "$PROJECT_ROOT/.env"
        log_success "Created secure .env file"
    else
        log_warning ".env file already exists, skipping generation"
    fi
}

# Install security tools
install_security_tools() {
    log_info "Installing security tools..."

    # Check if pip is available
    if ! command -v pip &> /dev/null; then
        log_error "pip is not installed. Please install Python and pip first."
        exit 1
    fi

    # Install security-related Python packages
    security_packages=(
        "bandit"
        "safety"
        "cryptography"
        "pyjwt"
        "passlib[bcrypt]"
    )

    for package in "${security_packages[@]}"; do
        if pip install "$package" &> /dev/null; then
            log_success "Installed $package"
        else
            log_warning "Failed to install $package"
        fi
    done
}

# Run security audit
run_security_audit() {
    log_info "Running security audit..."

    if [[ -f "$PROJECT_ROOT/security/hardening_scripts.py" ]]; then
        python3 "$PROJECT_ROOT/security/hardening_scripts.py" --environment "$ENVIRONMENT" --audit
        log_success "Security audit completed"
    else
        log_warning "Security hardening scripts not found, skipping audit"
    fi
}

# Configure SSL/TLS
configure_ssl() {
    log_info "Configuring SSL/TLS settings..."

    ssl_config_dir="$PROJECT_ROOT/security/ssl"
    mkdir -p "$ssl_config_dir"

    # Create SSL configuration
    cat > "$ssl_config_dir/ssl_config.conf" << EOF
# SSL/TLS Configuration for DevSkyy
# Generated on $(date)

# Minimum TLS version
ssl_protocols TLSv1.2 TLSv1.3;

# Cipher suites (strong encryption only)
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256;
ssl_prefer_server_ciphers on;

# SSL session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
EOF

    chmod 644 "$ssl_config_dir/ssl_config.conf"
    log_success "SSL/TLS configuration created"
}

# Main execution
main() {
    log_info "Starting DevSkyy Security Hardening Setup"
    log_info "Environment: $ENVIRONMENT"

    check_root
    create_security_dirs
    set_file_permissions
    generate_env_files
    install_security_tools
    configure_ssl
    run_security_audit

    log_success "Security hardening setup completed!"
    log_info "Next steps:"
    echo "  1. Review and update the generated .env file with your actual values"
    echo "  2. Configure your database and Redis connections"
    echo "  3. Add your AI service API keys"
    echo "  4. Set up SSL certificates for production"
    echo "  5. Run 'python security/hardening_scripts.py --audit' periodically"
}

# Run main function
main "$@"
