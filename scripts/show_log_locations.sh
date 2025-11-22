#!/bin/bash
# DevSkyy Log Locations Quick Reference
# Usage: bash scripts/show_log_locations.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 DevSkyy Error Log Locations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "⚠️  Logs directory does not exist yet"
    echo "💡 The logs directory will be created when you first run the application"
    echo ""
    echo "To create it now:"
    echo "  mkdir -p logs"
    echo ""
    exit 0
fi

echo "📁 Log Directory: $(pwd)/logs"
echo ""

# List log files with details
if [ -n "$(ls -A logs/*.log 2>/dev/null)" ]; then
    echo "📊 Available Log Files:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            filename=$(basename "$log_file")
            size=$(du -h "$log_file" | cut -f1)
            lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
            modified=$(date -r "$log_file" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || stat -c %y "$log_file" 2>/dev/null | cut -d'.' -f1)
            
            echo ""
            case "$filename" in
                devskyy.log)
                    echo "📄 $filename"
                    echo "   Purpose: Main application log (all levels)"
                    ;;
                error.log)
                    echo "🔴 $filename"
                    echo "   Purpose: Error-level logs only"
                    ;;
                security.log)
                    echo "🔒 $filename"
                    echo "   Purpose: Security events and audit trail"
                    ;;
                access.log)
                    echo "🌐 $filename"
                    echo "   Purpose: HTTP access logs"
                    ;;
                *)
                    echo "📝 $filename"
                    ;;
            esac
            
            echo "   Size: $size"
            echo "   Lines: $lines"
            echo "   Modified: $modified"
            echo "   Path: $(pwd)/$log_file"
        fi
    done
else
    echo "ℹ️  No log files found yet"
    echo ""
    echo "💡 Log files will be created when you run the application:"
    echo "   python main.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Quick Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View error logs:"
echo "  tail -n 50 logs/error.log"
echo ""
echo "Follow logs in real-time:"
echo "  tail -f logs/devskyy.log"
echo ""
echo "Interactive log viewer:"
echo "  python scripts/view_logs.py"
echo ""
echo "Search for errors:"
echo "  grep 'ERROR' logs/devskyy.log"
echo ""
echo "View security events:"
echo "  cat logs/security.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Complete logging guide: LOGGING_GUIDE.md"
echo "Quick start guide: QUICKSTART.md"
echo "README section: README.md (search for 'Logging')"
echo ""
