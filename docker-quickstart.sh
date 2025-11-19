#!/bin/bash

# ============================================================================
# DevSkyy Enterprise Platform - Docker Quick Start Script
# Version: 5.2.0
# Description: Automated Docker deployment with interactive setup
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.production.yml"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     DevSkyy Enterprise Platform - Docker Quick Start         ║"
    echo "║     Version 5.2.0                                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

check_requirements() {
    print_info "Checking requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker installed: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose installed: $(docker-compose --version)"

    # Check Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker daemon is running"

    echo ""
}

# ============================================================================
# Environment Setup
# ============================================================================

generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || \
    openssl rand -base64 32 2>/dev/null || \
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

setup_environment() {
    print_info "Setting up environment variables..."

    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Using existing .env file"
            return 0
        fi
    fi

    # Copy template
    if [ -f "${SCRIPT_DIR}/.env.production.example" ]; then
        cp "${SCRIPT_DIR}/.env.production.example" "$ENV_FILE"
    elif [ -f "${SCRIPT_DIR}/.env.example" ]; then
        cp "${SCRIPT_DIR}/.env.example" "$ENV_FILE"
    else
        print_error ".env.example not found"
        exit 1
    fi

    # Generate secrets
    print_info "Generating secure secrets..."
    SECRET_KEY=$(generate_secret)
    DB_PASSWORD=$(generate_secret)
    JWT_SECRET=$(generate_secret)

    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE"
        sed -i '' "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASSWORD}|g" "$ENV_FILE"
        sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|g" "$ENV_FILE"
        sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=postgresql://devskyy:${DB_PASSWORD}@postgres:5432/devskyy|g" "$ENV_FILE"
    else
        # Linux
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE"
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASSWORD}|g" "$ENV_FILE"
        sed -i "s|JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|g" "$ENV_FILE"
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://devskyy:${DB_PASSWORD}@postgres:5432/devskyy|g" "$ENV_FILE"
    fi

    print_success "Environment file created: $ENV_FILE"
    print_warning "Please edit .env and add your API keys:"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - OPENAI_API_KEY"
    echo ""

    read -p "Press Enter to continue after editing .env..."
}

# ============================================================================
# Deployment Functions
# ============================================================================

build_images() {
    print_info "Building Docker images..."

    cd "$SCRIPT_DIR"

    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" build
    else
        docker-compose build
    fi

    print_success "Docker images built successfully"
    echo ""
}

start_services() {
    print_info "Starting services..."

    cd "$SCRIPT_DIR"

    # Ask what to start
    echo "Select deployment mode:"
    echo "1) Production (API + PostgreSQL + Redis + Nginx + Monitoring)"
    echo "2) Basic (API + PostgreSQL + Redis only)"
    echo "3) Development (API + PostgreSQL + Redis with hot reload)"
    read -p "Enter choice [1-3]: " -n 1 -r
    echo

    case $REPLY in
        1)
            print_info "Starting production stack..."
            if [ -f "$COMPOSE_FILE" ]; then
                docker-compose -f "$COMPOSE_FILE" up -d
            else
                docker-compose up -d
            fi
            ;;
        2)
            print_info "Starting basic stack..."
            docker-compose up -d devskyy postgres redis
            ;;
        3)
            print_info "Starting development stack..."
            docker-compose up -d
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    print_success "Services started"
    echo ""
}

wait_for_health() {
    print_info "Waiting for services to be healthy..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    print_error "API health check timeout"
    print_info "Check logs: docker-compose logs api"
    return 1
}

show_status() {
    print_info "Container Status:"
    docker-compose ps
    echo ""

    print_info "Service URLs:"
    echo "  API:        http://localhost:8000"
    echo "  API Docs:   http://localhost:8000/api/v1/docs"
    echo "  Health:     http://localhost:8000/health"
    echo "  Grafana:    http://localhost:3000 (if monitoring enabled)"
    echo "  Prometheus: http://localhost:9090 (if monitoring enabled)"
    echo ""

    print_info "Useful Commands:"
    echo "  View logs:     docker-compose logs -f api"
    echo "  Stop all:      docker-compose down"
    echo "  Restart API:   docker-compose restart api"
    echo "  Shell access:  docker-compose exec api bash"
    echo ""
}

# ============================================================================
# Main Menu
# ============================================================================

show_menu() {
    echo "What would you like to do?"
    echo "1) Quick Start (Setup + Build + Deploy)"
    echo "2) Setup Environment Only"
    echo "3) Build Images Only"
    echo "4) Start Services Only"
    echo "5) Stop All Services"
    echo "6) View Status"
    echo "7) View Logs"
    echo "8) Clean Up (Remove all containers and volumes)"
    echo "9) Exit"
    echo ""
    read -p "Enter choice [1-9]: " choice

    case $choice in
        1)
            check_requirements
            setup_environment
            build_images
            start_services
            wait_for_health
            show_status
            ;;
        2)
            setup_environment
            ;;
        3)
            build_images
            ;;
        4)
            start_services
            wait_for_health
            show_status
            ;;
        5)
            print_info "Stopping all services..."
            docker-compose down
            print_success "All services stopped"
            ;;
        6)
            show_status
            ;;
        7)
            read -p "Which service? (api/postgres/redis/all): " service
            if [ "$service" == "all" ]; then
                docker-compose logs -f
            else
                docker-compose logs -f "$service"
            fi
            ;;
        8)
            print_warning "This will remove all containers, networks, and volumes!"
            read -p "Are you sure? (yes/NO): " confirm
            if [ "$confirm" == "yes" ]; then
                docker-compose down -v
                print_success "Cleanup complete"
            else
                print_info "Cleanup cancelled"
            fi
            ;;
        9)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header

    # If arguments provided, run specific action
    if [ $# -gt 0 ]; then
        case $1 in
            start)
                check_requirements
                start_services
                wait_for_health
                show_status
                ;;
            stop)
                docker-compose down
                ;;
            restart)
                docker-compose restart
                ;;
            status)
                show_status
                ;;
            logs)
                docker-compose logs -f ${2:-api}
                ;;
            clean)
                docker-compose down -v
                ;;
            *)
                echo "Usage: $0 {start|stop|restart|status|logs|clean}"
                exit 1
                ;;
        esac
    else
        # Interactive mode
        while true; do
            show_menu
            echo ""
            read -p "Continue? (Y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                break
            fi
        done
    fi

    print_success "Done!"
}

# Run main function
main "$@"
