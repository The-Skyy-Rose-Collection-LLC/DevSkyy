#!/bin/bash
# Quick Neon Configuration Helper for DevSkyy
# This script helps you configure Neon credentials interactively

echo "🌹 DevSkyy - Neon Configuration Helper"
echo "========================================"
echo ""
echo "This will help you configure Neon PostgreSQL for DevSkyy."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

echo ""
echo "📝 You need 3 things from Neon:"
echo ""
echo "1. DATABASE_URL (Connection String)"
echo "   Get from: Your Neon Project Dashboard"
echo "   Looks like: postgresql://user:pass@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require"
echo ""
echo "2. NEON_API_KEY"
echo "   Get from: https://console.neon.tech/app/settings/api-keys"
echo "   Looks like: a long string of characters"
echo ""
echo "3. NEON_PROJECT_ID"
echo "   Get from: Project Settings or URL"
echo "   Looks like: ep-xxx-xxx-xxx"
echo ""

# Option to open Neon console
read -p "❓ Do you want to open Neon console in browser? (y/n): " open_browser
if [[ $open_browser == "y" || $open_browser == "Y" ]]; then
    echo "🌐 Opening Neon console..."

    # Try to open browser based on OS
    if command -v xdg-open > /dev/null; then
        xdg-open https://console.neon.tech 2>/dev/null &
    elif command -v open > /dev/null; then
        open https://console.neon.tech 2>/dev/null &
    else
        echo "   Please manually open: https://console.neon.tech"
    fi
fi

echo ""
echo "📋 Configuration Instructions:"
echo ""
echo "Option 1 - Manual Configuration:"
echo "   1. Edit .env file: nano .env"
echo "   2. Find the NEON section (near the bottom)"
echo "   3. Replace the placeholder values with your actual Neon credentials"
echo "   4. Save and exit (Ctrl+O, Enter, Ctrl+X in nano)"
echo ""
echo "Option 2 - Interactive Configuration:"
echo "   We can configure it now if you have your credentials ready."
echo ""

read -p "❓ Do you have your Neon credentials ready? (y/n): " has_credentials

if [[ $has_credentials == "y" || $has_credentials == "Y" ]]; then
    echo ""
    echo "Great! Let's configure your Neon credentials..."
    echo ""

    # Get DATABASE_URL with validation
    echo "📝 DATABASE_URL:"
    echo "   (Example: postgresql://user:pass@ep-xxx-xxx.us-east-2.aws.neon.tech/devskyy?sslmode=require)"
    database_url=""
    attempts=0
    max_attempts=3
    while [[ -z "$database_url" || ! "$database_url" =~ ^postgresql:// ]]; do
        read -p "   Enter your DATABASE_URL: " database_url
        if [[ -z "$database_url" ]]; then
            echo "   ❌ ERROR: DATABASE_URL cannot be empty"
            ((attempts++))
        elif [[ ! "$database_url" =~ ^postgresql:// ]]; then
            echo "   ❌ ERROR: DATABASE_URL must start with 'postgresql://'"
            ((attempts++))
        fi
        if [[ $attempts -ge $max_attempts ]]; then
            echo "   ❌ Maximum attempts reached. Exiting."
            exit 1
        fi
    done

    # Get NEON_API_KEY with validation
    echo ""
    echo "📝 NEON_API_KEY:"
    neon_api_key=""
    attempts=0
    while [[ -z "$neon_api_key" || ${#neon_api_key} -lt 10 ]]; do
        read -p "   Enter your API key: " neon_api_key
        if [[ -z "$neon_api_key" ]]; then
            echo "   ❌ ERROR: NEON_API_KEY cannot be empty"
            ((attempts++))
        elif [[ ${#neon_api_key} -lt 10 ]]; then
            echo "   ❌ ERROR: NEON_API_KEY seems too short (must be at least 10 characters)"
            ((attempts++))
        fi
        if [[ $attempts -ge $max_attempts ]]; then
            echo "   ❌ Maximum attempts reached. Exiting."
            exit 1
        fi
    done

    # Get NEON_PROJECT_ID with validation
    echo ""
    echo "📝 NEON_PROJECT_ID:"
    neon_project_id=""
    attempts=0
    while [[ -z "$neon_project_id" ]]; do
        read -p "   Enter your project ID: " neon_project_id
        if [[ -z "$neon_project_id" ]]; then
            echo "   ❌ ERROR: NEON_PROJECT_ID cannot be empty"
            ((attempts++))
        fi
        if [[ $attempts -ge $max_attempts ]]; then
            echo "   ❌ Maximum attempts reached. Exiting."
            exit 1
        fi
    done

    # Update .env file
    echo ""
    echo "💾 Updating .env file..."

    # Escape special characters for sed (& | / \)
    database_url_escaped=$(printf '%s\n' "$database_url" | sed 's/[&/\]/\\&/g')
    neon_api_key_escaped=$(printf '%s\n' "$neon_api_key" | sed 's/[&/\]/\\&/g')
    neon_project_id_escaped=$(printf '%s\n' "$neon_project_id" | sed 's/[&/\]/\\&/g')

    # Use sed to replace placeholders
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|DATABASE_URL=postgresql://user:password@ep-your-project.us-east-2.aws.neon.tech/devskyy?sslmode=require|DATABASE_URL=$database_url_escaped|g" .env
        sed -i '' "s|NEON_API_KEY=your_neon_api_key_here|NEON_API_KEY=$neon_api_key_escaped|g" .env
        sed -i '' "s|NEON_PROJECT_ID=your_project_id_here|NEON_PROJECT_ID=$neon_project_id_escaped|g" .env
    else
        # Linux
        sed -i "s|DATABASE_URL=postgresql://user:password@ep-your-project.us-east-2.aws.neon.tech/devskyy?sslmode=require|DATABASE_URL=$database_url_escaped|g" .env
        sed -i "s|NEON_API_KEY=your_neon_api_key_here|NEON_API_KEY=$neon_api_key_escaped|g" .env
        sed -i "s|NEON_PROJECT_ID=your_project_id_here|NEON_PROJECT_ID=$neon_project_id_escaped|g" .env
    fi

    echo "✅ Configuration saved!"
    echo ""
    echo "🧪 Testing connection..."

    # Test with neon_manager.py
    if python scripts/neon_manager.py project-info 2>&1 | grep -q "Project Information"; then
        echo "✅ Connection successful!"
        echo ""
        echo "🎉 Neon is configured and working!"
        echo ""
        echo "Next steps:"
        echo "  1. Create environment branches: python scripts/neon_manager.py create-branches"
        echo "  2. Start DevSkyy: docker-compose -f docker-compose.dev.yml up -d"
        echo "  3. Check health: curl http://localhost:8000/health"
    else
        echo "⚠️  Could not verify connection. Please check your credentials."
        echo ""
        echo "Troubleshooting:"
        echo "  1. Verify credentials in Neon console"
        echo "  2. Check .env file: cat .env | grep NEON"
        echo "  3. Test manually: python scripts/neon_manager.py project-info"
    fi
else
    echo ""
    echo "📖 No problem! Here's what to do:"
    echo ""
    echo "1. Sign up for Neon: https://neon.tech"
    echo "2. Create a project named 'devskyy'"
    echo "3. Get your credentials from the dashboard"
    echo "4. Run this script again: bash scripts/configure_neon.sh"
    echo ""
    echo "Or manually edit .env:"
    echo "   nano .env"
    echo ""
fi

echo ""
echo "📚 Need help? Check:"
echo "   - NEON_INTEGRATION_GUIDE.md (comprehensive guide)"
echo "   - https://neon.tech/docs (Neon documentation)"
echo ""
echo "✨ Done!"
