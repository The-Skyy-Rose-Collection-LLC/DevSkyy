#!/bin/bash

################################################################################
# DevSkyy Monitoring Performance Baseline Collection
# Purpose: Collect performance metrics over 30 minutes to establish baseline
# Usage: ./monitoring_performance_baseline.sh [duration_minutes]
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
DURATION_MINUTES="${1:-30}"  # Default 30 minutes, can be overridden
SAMPLE_INTERVAL=60           # Sample every 60 seconds

# Logging
LOG_DIR="./monitoring_logs"
mkdir -p "$LOG_DIR"
BASELINE_REPORT="$LOG_DIR/performance_baseline_report_$(date +%Y%m%d_%H%M%S).txt"
BASELINE_JSON="$LOG_DIR/performance_baseline_report_$(date +%Y%m%d_%H%M%S).json"
METRICS_DATA="$LOG_DIR/metrics_data_$(date +%Y%m%d_%H%M%S).csv"

# Metrics arrays
declare -a TIMESTAMPS
declare -a API_LATENCY_P50
declare -a API_LATENCY_P95
declare -a API_LATENCY_P99
declare -a RATE_LIMIT_PERFORMANCE
declare -a MEMORY_USAGE
declare -a CPU_USAGE
declare -a ERROR_RATE

################################################################################
# Utility Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$BASELINE_REPORT"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$BASELINE_REPORT"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$BASELINE_REPORT"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$BASELINE_REPORT"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

query_prometheus() {
    local query=$1
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$(echo $query | jq -sRr @uri)" | jq -r '.data.result[0].value[1]')

    # Handle cases where no data is returned
    if [ "$result" == "null" ] || [ -z "$result" ]; then
        echo "0"
    else
        echo "$result"
    fi
}

format_duration() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local remaining_seconds=$((seconds % 60))
    echo "${minutes}m ${remaining_seconds}s"
}

################################################################################
# Metrics Collection Functions
################################################################################

collect_api_latency_metrics() {
    log_info "Collecting API latency metrics..."

    # P50 (median)
    local p50_query='histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[1m]))'
    local p50=$(query_prometheus "$p50_query")
    API_LATENCY_P50+=("$p50")

    # P95
    local p95_query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))'
    local p95=$(query_prometheus "$p95_query")
    API_LATENCY_P95+=("$p95")

    # P99
    local p99_query='histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[1m]))'
    local p99=$(query_prometheus "$p99_query")
    API_LATENCY_P99+=("$p99")

    log_info "  P50: ${p50}s | P95: ${p95}s | P99: ${p99}s"
}

collect_rate_limit_performance() {
    log_info "Collecting rate limit performance..."

    # Rate limit check duration
    local rate_limit_query='rate(rate_limit_check_duration_seconds_sum[1m]) / rate(rate_limit_check_duration_seconds_count[1m])'
    local rate_limit_perf=$(query_prometheus "$rate_limit_query")
    RATE_LIMIT_PERFORMANCE+=("$rate_limit_perf")

    log_info "  Rate limit check avg: ${rate_limit_perf}s"
}

collect_memory_usage() {
    log_info "Collecting memory usage metrics..."

    # Memory usage percentage
    local memory_query='(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100'
    local memory_usage=$(query_prometheus "$memory_query")
    MEMORY_USAGE+=("$memory_usage")

    log_info "  Memory usage: ${memory_usage}%"
}

collect_cpu_usage() {
    log_info "Collecting CPU usage metrics..."

    # CPU usage percentage
    local cpu_query='100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    local cpu_usage=$(query_prometheus "$cpu_query")
    CPU_USAGE+=("$cpu_usage")

    log_info "  CPU usage: ${cpu_usage}%"
}

collect_error_rate() {
    log_info "Collecting error rate metrics..."

    # HTTP 5xx error rate
    local error_query='sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m])) * 100'
    local error_rate=$(query_prometheus "$error_query")
    ERROR_RATE+=("$error_rate")

    log_info "  Error rate: ${error_rate}%"
}

collect_all_metrics() {
    local timestamp=$(date +%s)
    TIMESTAMPS+=("$timestamp")

    collect_api_latency_metrics
    collect_rate_limit_performance
    collect_memory_usage
    collect_cpu_usage
    collect_error_rate

    log_info "Sample collected at $(date)"
}

################################################################################
# Statistics Functions
################################################################################

calculate_mean() {
    local -n arr=$1
    local sum=0
    local count=${#arr[@]}

    if [ $count -eq 0 ]; then
        echo "0"
        return
    fi

    for val in "${arr[@]}"; do
        sum=$(echo "$sum + $val" | bc -l)
    done

    echo "scale=6; $sum / $count" | bc -l
}

calculate_min() {
    local -n arr=$1
    local min=${arr[0]}

    for val in "${arr[@]}"; do
        if (( $(echo "$val < $min" | bc -l) )); then
            min=$val
        fi
    done

    echo "$min"
}

calculate_max() {
    local -n arr=$1
    local max=${arr[0]}

    for val in "${arr[@]}"; do
        if (( $(echo "$val > $max" | bc -l) )); then
            max=$val
        fi
    done

    echo "$max"
}

calculate_std_dev() {
    local -n arr=$1
    local mean=$2
    local sum_sq_diff=0
    local count=${#arr[@]}

    if [ $count -eq 0 ]; then
        echo "0"
        return
    fi

    for val in "${arr[@]}"; do
        local diff=$(echo "$val - $mean" | bc -l)
        local sq_diff=$(echo "$diff * $diff" | bc -l)
        sum_sq_diff=$(echo "$sum_sq_diff + $sq_diff" | bc -l)
    done

    local variance=$(echo "scale=6; $sum_sq_diff / $count" | bc -l)
    echo "scale=6; sqrt($variance)" | bc -l
}

################################################################################
# Data Export
################################################################################

export_csv_data() {
    print_header "Exporting CSV Data"

    log_info "Writing metrics to CSV: $METRICS_DATA"

    # Write header
    echo "timestamp,api_p50,api_p95,api_p99,rate_limit_perf,memory_usage,cpu_usage,error_rate" > "$METRICS_DATA"

    # Write data rows
    for i in "${!TIMESTAMPS[@]}"; do
        echo "${TIMESTAMPS[$i]},${API_LATENCY_P50[$i]},${API_LATENCY_P95[$i]},${API_LATENCY_P99[$i]},${RATE_LIMIT_PERFORMANCE[$i]},${MEMORY_USAGE[$i]},${CPU_USAGE[$i]},${ERROR_RATE[$i]}" >> "$METRICS_DATA"
    done

    log_success "CSV data exported successfully"
}

################################################################################
# Analysis & Reporting
################################################################################

analyze_metrics() {
    print_header "Analyzing Performance Baseline"

    local sample_count=${#TIMESTAMPS[@]}
    log_info "Total samples collected: $sample_count"

    # API Latency Analysis
    echo "" | tee -a "$BASELINE_REPORT"
    echo "API Request Latency:" | tee -a "$BASELINE_REPORT"
    echo "-------------------" | tee -a "$BASELINE_REPORT"

    local p50_mean=$(calculate_mean API_LATENCY_P50)
    local p50_min=$(calculate_min API_LATENCY_P50)
    local p50_max=$(calculate_max API_LATENCY_P50)
    local p50_std=$(calculate_std_dev API_LATENCY_P50 $p50_mean)

    echo "P50 (Median):" | tee -a "$BASELINE_REPORT"
    echo "  Mean: ${p50_mean}s" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${p50_min}s" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${p50_max}s" | tee -a "$BASELINE_REPORT"
    echo "  StdDev: ${p50_std}s" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    local p95_mean=$(calculate_mean API_LATENCY_P95)
    local p95_min=$(calculate_min API_LATENCY_P95)
    local p95_max=$(calculate_max API_LATENCY_P95)
    local p95_std=$(calculate_std_dev API_LATENCY_P95 $p95_mean)

    echo "P95:" | tee -a "$BASELINE_REPORT"
    echo "  Mean: ${p95_mean}s" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${p95_min}s" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${p95_max}s" | tee -a "$BASELINE_REPORT"
    echo "  StdDev: ${p95_std}s" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    local p99_mean=$(calculate_mean API_LATENCY_P99)
    local p99_min=$(calculate_min API_LATENCY_P99)
    local p99_max=$(calculate_max API_LATENCY_P99)
    local p99_std=$(calculate_std_dev API_LATENCY_P99 $p99_mean)

    echo "P99:" | tee -a "$BASELINE_REPORT"
    echo "  Mean: ${p99_mean}s" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${p99_min}s" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${p99_max}s" | tee -a "$BASELINE_REPORT"
    echo "  StdDev: ${p99_std}s" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    # Rate Limiting Performance
    echo "Rate Limiting Performance:" | tee -a "$BASELINE_REPORT"
    echo "-------------------------" | tee -a "$BASELINE_REPORT"

    local rl_mean=$(calculate_mean RATE_LIMIT_PERFORMANCE)
    local rl_min=$(calculate_min RATE_LIMIT_PERFORMANCE)
    local rl_max=$(calculate_max RATE_LIMIT_PERFORMANCE)

    echo "  Mean: ${rl_mean}s" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${rl_min}s" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${rl_max}s" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    # Memory/CPU Usage
    echo "Resource Usage:" | tee -a "$BASELINE_REPORT"
    echo "--------------" | tee -a "$BASELINE_REPORT"

    local mem_mean=$(calculate_mean MEMORY_USAGE)
    local mem_min=$(calculate_min MEMORY_USAGE)
    local mem_max=$(calculate_max MEMORY_USAGE)

    echo "Memory Usage:" | tee -a "$BASELINE_REPORT"
    echo "  Mean: ${mem_mean}%" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${mem_min}%" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${mem_max}%" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    local cpu_mean=$(calculate_mean CPU_USAGE)
    local cpu_min=$(calculate_min CPU_USAGE)
    local cpu_max=$(calculate_max CPU_USAGE)

    echo "CPU Usage:" | tee -a "$BASELINE_REPORT"
    echo "  Mean: ${cpu_mean}%" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${cpu_min}%" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${cpu_max}%" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    # Error Rates
    echo "Error Rates:" | tee -a "$BASELINE_REPORT"
    echo "-----------" | tee -a "$BASELINE_REPORT"

    local err_mean=$(calculate_mean ERROR_RATE)
    local err_min=$(calculate_min ERROR_RATE)
    local err_max=$(calculate_max ERROR_RATE)

    echo "  Mean: ${err_mean}%" | tee -a "$BASELINE_REPORT"
    echo "  Min:  ${err_min}%" | tee -a "$BASELINE_REPORT"
    echo "  Max:  ${err_max}%" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"

    # Store statistics for JSON report
    STATS_P50_MEAN="$p50_mean"
    STATS_P95_MEAN="$p95_mean"
    STATS_P99_MEAN="$p99_mean"
    STATS_RL_MEAN="$rl_mean"
    STATS_MEM_MEAN="$mem_mean"
    STATS_CPU_MEAN="$cpu_mean"
    STATS_ERR_MEAN="$err_mean"
}

generate_json_report() {
    print_header "Generating JSON Report"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local start_time="${TIMESTAMPS[0]}"
    local end_time="${TIMESTAMPS[-1]}"

    cat > "$BASELINE_JSON" <<EOF
{
  "timestamp": "$timestamp",
  "collection_period": {
    "start": "$start_time",
    "end": "$end_time",
    "duration_minutes": $DURATION_MINUTES,
    "sample_count": ${#TIMESTAMPS[@]},
    "sample_interval_seconds": $SAMPLE_INTERVAL
  },
  "performance_baseline": {
    "api_latency": {
      "p50": {
        "mean": $STATS_P50_MEAN,
        "unit": "seconds"
      },
      "p95": {
        "mean": $STATS_P95_MEAN,
        "unit": "seconds"
      },
      "p99": {
        "mean": $STATS_P99_MEAN,
        "unit": "seconds"
      }
    },
    "rate_limiting": {
      "check_duration_mean": $STATS_RL_MEAN,
      "unit": "seconds"
    },
    "resource_usage": {
      "memory": {
        "mean": $STATS_MEM_MEAN,
        "unit": "percent"
      },
      "cpu": {
        "mean": $STATS_CPU_MEAN,
        "unit": "percent"
      }
    },
    "error_rate": {
      "mean": $STATS_ERR_MEAN,
      "unit": "percent"
    }
  },
  "data_file": "$METRICS_DATA"
}
EOF

    log_success "JSON report saved to: $BASELINE_JSON"
}

generate_summary() {
    print_header "Performance Baseline Summary"

    echo "" | tee -a "$BASELINE_REPORT"
    echo "============================================" | tee -a "$BASELINE_REPORT"
    echo "PERFORMANCE BASELINE COLLECTION COMPLETE" | tee -a "$BASELINE_REPORT"
    echo "============================================" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"
    echo "Duration: $DURATION_MINUTES minutes" | tee -a "$BASELINE_REPORT"
    echo "Samples: ${#TIMESTAMPS[@]}" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"
    echo "Key Metrics:" | tee -a "$BASELINE_REPORT"
    echo "  API Latency (P95): ${STATS_P95_MEAN}s" | tee -a "$BASELINE_REPORT"
    echo "  Memory Usage: ${STATS_MEM_MEAN}%" | tee -a "$BASELINE_REPORT"
    echo "  CPU Usage: ${STATS_CPU_MEAN}%" | tee -a "$BASELINE_REPORT"
    echo "  Error Rate: ${STATS_ERR_MEAN}%" | tee -a "$BASELINE_REPORT"
    echo "" | tee -a "$BASELINE_REPORT"
    echo "Reports saved to:" | tee -a "$BASELINE_REPORT"
    echo "  Text: $BASELINE_REPORT" | tee -a "$BASELINE_REPORT"
    echo "  JSON: $BASELINE_JSON" | tee -a "$BASELINE_REPORT"
    echo "  CSV:  $METRICS_DATA" | tee -a "$BASELINE_REPORT"
    echo "============================================" | tee -a "$BASELINE_REPORT"
}

################################################################################
# Main Collection Loop
################################################################################

main() {
    print_header "DevSkyy Performance Baseline Collection"

    log_info "Starting performance baseline collection"
    log_info "Duration: $DURATION_MINUTES minutes"
    log_info "Sample interval: $SAMPLE_INTERVAL seconds"
    log_info "Prometheus URL: $PROMETHEUS_URL"
    echo ""

    # Calculate total samples
    local total_samples=$((DURATION_MINUTES * 60 / SAMPLE_INTERVAL))
    log_info "Total samples to collect: $total_samples"
    echo ""

    # Check Prometheus connectivity
    log_info "Checking Prometheus connectivity..."
    if ! curl -s -f "$PROMETHEUS_URL/-/healthy" > /dev/null 2>&1; then
        log_error "Cannot connect to Prometheus at $PROMETHEUS_URL"
        exit 1
    fi
    log_success "Connected to Prometheus"
    echo ""

    # Collection loop
    local start_time=$(date +%s)
    local end_time=$((start_time + (DURATION_MINUTES * 60)))
    local sample_num=0

    while [ $(date +%s) -lt $end_time ]; do
        ((sample_num++))
        local elapsed=$(($(date +%s) - start_time))
        local remaining=$((end_time - $(date +%s)))

        print_header "Sample $sample_num/$total_samples (Elapsed: $(format_duration $elapsed), Remaining: $(format_duration $remaining))"

        collect_all_metrics

        # Don't sleep after last sample
        if [ $(date +%s) -lt $end_time ]; then
            log_info "Waiting $SAMPLE_INTERVAL seconds until next sample..."
            sleep $SAMPLE_INTERVAL
        fi
    done

    # Analysis and reporting
    export_csv_data
    analyze_metrics
    generate_json_report
    generate_summary

    log_success "Performance baseline collection completed successfully"
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n\n${YELLOW}Collection interrupted by user${NC}\n"; exit 130' INT

# Run main function
main "$@"
