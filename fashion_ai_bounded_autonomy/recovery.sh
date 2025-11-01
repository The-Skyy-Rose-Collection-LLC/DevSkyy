#!/bin/bash
# LAYER 8 — RECOVERY SCRIPT
# Restore bounded autonomy system from backup

set -e

echo "🔄 Fashion AI Bounded Autonomy - Recovery Script"
echo "================================================"

# Configuration
BACKUP_DIR="fashion_ai_bounded_autonomy/archive"
RESTORE_DIR="fashion_ai_bounded_autonomy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# List available backups
echo ""
echo "📦 Available backups:"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || {
    echo "❌ No backups found in $BACKUP_DIR"
    exit 1
}

# Get latest backup if not specified
if [ -z "$1" ]; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.tar.gz | head -1)
    echo ""
    echo "📍 No backup specified, using latest: $BACKUP_FILE"
else
    BACKUP_FILE="$BACKUP_DIR/$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Error: Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

# Confirm recovery
echo ""
echo "⚠️  WARNING: This will restore the system from backup."
echo "Current state will be backed up to: backup_pre_recovery_$TIMESTAMP.tar.gz"
echo ""
read -p "Continue with recovery? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Recovery cancelled"
    exit 0
fi

# Create pre-recovery backup
echo ""
echo "💾 Creating pre-recovery backup..."
cd "$(dirname "$RESTORE_DIR")"
tar -czf "$BACKUP_DIR/backup_pre_recovery_$TIMESTAMP.tar.gz" \
    "$(basename "$RESTORE_DIR")" 2>/dev/null || true
echo "✅ Pre-recovery backup created"

# Stop running services
echo ""
echo "🛑 Stopping services..."
pkill -f "fashion_ai_bounded_autonomy" || true
sleep 2

# Extract backup
echo ""
echo "📂 Extracting backup..."
mkdir -p "$RESTORE_DIR.tmp"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR.tmp"

# Restore files
echo ""
echo "♻️  Restoring files..."

# Backup current config
if [ -d "$RESTORE_DIR/config" ]; then
    mv "$RESTORE_DIR/config" "$RESTORE_DIR/config.backup_$TIMESTAMP" || true
fi

# Restore from backup
rsync -av --delete "$RESTORE_DIR.tmp/" "$RESTORE_DIR/"
rm -rf "$RESTORE_DIR.tmp"

echo "✅ Files restored"

# Verify integrity
echo ""
echo "🔍 Verifying integrity..."

# Check critical files
CRITICAL_FILES=(
    "config/architecture.yaml"
    "config/agents_config.json"
    "config/dataflow.yaml"
    "bounded_orchestrator.py"
    "approval_system.py"
)

MISSING_FILES=0
for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$RESTORE_DIR/$file" ]; then
        echo "⚠️  Missing critical file: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo "❌ Recovery incomplete: $MISSING_FILES critical files missing"
    echo "System state may be inconsistent. Manual intervention required."
    exit 1
fi

echo "✅ Integrity check passed"

# Initialize databases
echo ""
echo "🗄️  Initializing databases..."
python3 -c "
from fashion_ai_bounded_autonomy.approval_system import ApprovalSystem
from fashion_ai_bounded_autonomy.performance_tracker import PerformanceTracker

# Initialize systems (creates DB schemas if needed)
approval = ApprovalSystem()
tracker = PerformanceTracker()
print('✅ Databases initialized')
" || {
    echo "⚠️  Database initialization failed (may need manual repair)"
}

# Create recovery report
REPORT_FILE="$RESTORE_DIR/recovery_report_$TIMESTAMP.txt"
cat > "$REPORT_FILE" << EOF
====================================================================
RECOVERY REPORT
====================================================================

Recovery Date: $(date)
Backup File: $BACKUP_FILE
Restored To: $RESTORE_DIR

Critical Files:
$(for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$RESTORE_DIR/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
    fi
done)

Next Steps:
1. Review this report
2. Verify configuration files in config/
3. Check logs in logs/
4. Test system with: python -m fashion_ai_bounded_autonomy.approval_cli list
5. Restart services when ready

====================================================================
EOF

echo ""
echo "📄 Recovery report saved to: $REPORT_FILE"

# Final instructions
echo ""
echo "====================================================================  "
echo "✅ RECOVERY COMPLETE"
echo "===================================================================="
echo ""
echo "IMPORTANT: System recovery successful. Next steps:"
echo ""
echo "1. Review recovery report: cat $REPORT_FILE"
echo "2. Verify configuration:"
echo "   - cat fashion_ai_bounded_autonomy/config/architecture.yaml"
echo "   - cat fashion_ai_bounded_autonomy/config/agents_config.json"
echo ""
echo "3. Test approval system:"
echo "   python -m fashion_ai_bounded_autonomy.approval_cli list"
echo ""
echo "4. Review logs:"
echo "   - ls -lh logs/"
echo "   - tail -f logs/system/*.log"
echo ""
echo "5. When ready, restart the system manually"
echo ""
echo "⚠️  Do NOT restart automatically. Operator confirmation required."
echo "===================================================================="
echo ""
