#!/bin/bash
# Script to run the complete CAD-Coder pipeline and save output to log file
#
# Usage:
#   ./run_and_log.sh [LOG_FILENAME]
#
# If no filename provided, defaults to PIPELINE_RUN.log

LOG_FILE="${1:-PIPELINE_RUN.log}"

echo "============================================================"
echo "🚀 Running CAD-Coder End-to-End Pipeline"
echo "============================================================"
echo "📝 Log file: $LOG_FILE"
echo "⏱️  Start time: $(date)"
echo ""

# Run docker-compose and tee output to log file
docker-compose up 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "============================================================"
echo "✅ Pipeline Complete"
echo "============================================================"
echo "⏱️  End time: $(date)"
echo "📊 Exit code: $EXIT_CODE"
echo "📝 Log saved to: $LOG_FILE"
echo "📏 Log size: $(du -h "$LOG_FILE" | cut -f1)"
echo "📄 Log lines: $(wc -l < "$LOG_FILE")"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All services completed successfully!"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "   Check $LOG_FILE for details"
fi

exit $EXIT_CODE

