#!/bin/bash

# Script to run all RAG pipeline tests and log output to a single file

LOG_FILE="test_results.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "================================================================================" > "$LOG_FILE"
echo "RAG Pipeline Test Run - $TIMESTAMP" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "Running RAG pipeline tests..."
echo "Output will be saved to: $LOG_FILE"
echo ""

# Test 1: Metadata test
echo "================================================================================" >> "$LOG_FILE"
echo "TEST 1: Metadata Retrieval Verification" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "[1/3] Running metadata test..."
docker-compose run --rm rag-pipeline python -W ignore test_rag.py metadata >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Test 2: Single text query
echo "================================================================================" >> "$LOG_FILE"
echo "TEST 2: Single Text Query" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "[2/3] Running single text query test..."
docker-compose run --rm rag-pipeline python -W ignore test_rag.py single >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Test 3: Multimodal query
echo "================================================================================" >> "$LOG_FILE"
echo "TEST 3: Multimodal Query (Text + Image)" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "[3/3] Running multimodal query test..."
docker-compose run --rm rag-pipeline python -W ignore test_rag.py multimodal >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Summary
echo "================================================================================" >> "$LOG_FILE"
echo "Test Run Complete - $(date "+%Y-%m-%d %H:%M:%S")" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"

echo ""
echo "✅ All tests completed!"
echo "📄 Results saved to: $LOG_FILE"
echo ""
echo "To view results:"
echo "  cat $LOG_FILE"
echo "  or"
echo "  less $LOG_FILE"

