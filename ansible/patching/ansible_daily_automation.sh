#!/bin/bash
#
# Ansible Daily Automation Script
# Orchestrates: Asset Discovery, Patch Status Reporting, and Optional Patching
#

set -euo pipefail

# Configuration
ANSIBLE_DIR="/opt/ansible"
LOG_DIR="/var/log/ansible-automation"
REPORT_DIR="$ANSIBLE_DIR/reports"
AUTOMATION_LOG="$LOG_DIR/daily-automation.log"
EMAIL_RECIPIENT="root@localhost"  # Change to your email
AUTO_PATCH_ENABLED="${AUTO_PATCH_ENABLED:-false}"  # Set to true for automatic patching

# Ensure directories exist
mkdir -p "$LOG_DIR" "$REPORT_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$AUTOMATION_LOG"
}

# Send notification (via mail or log)
send_notification() {
    local subject="$1"
    local message="$2"
    local report_file="$3"

    log "$subject"
    log "$message"

    # If mail is configured, send email
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$EMAIL_RECIPIENT" -A "$report_file" 2>&1 | tee -a "$AUTOMATION_LOG"
    fi
}

# Step 1: Asset Auto-Discovery
run_asset_discovery() {
    log "========================================="
    log "Step 1: Running Asset Auto-Discovery"
    log "========================================="

    if [ -x /usr/local/bin/ansible-auto-discovery.sh ]; then
        /usr/local/bin/ansible-auto-discovery.sh 2>&1 | tee -a "$AUTOMATION_LOG"

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log "Asset discovery completed successfully"
            return 0
        else
            log "ERROR: Asset discovery failed"
            return 1
        fi
    else
        log "WARNING: Auto-discovery script not found, skipping"
        return 0
    fi
}

# Step 2: Generate Patch Status Report
run_patch_status_report() {
    log "========================================="
    log "Step 2: Generating Patch Status Report"
    log "========================================="

    cd "$ANSIBLE_DIR"

    ansible-playbook \
        -i inventories/homelab.yml \
        playbooks/patch_status_report.yml \
        --limit '!truenas' \
        2>&1 | tee -a "$AUTOMATION_LOG"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "Patch status report generated successfully"

        # Find the latest report
        LATEST_REPORT=$(ls -t "$REPORT_DIR"/patch-status-*.html 2>/dev/null | head -1)

        if [ -n "$LATEST_REPORT" ]; then
            log "Report available at: $LATEST_REPORT"

            # Count hosts needing patches
            HOSTS_NEEDING_PATCHES=$(grep -oP 'Hosts Requiring Updates.*?<span class="warning">\K\d+' "$LATEST_REPORT" || echo "0")

            send_notification \
                "Homelab Patch Status Report" \
                "Daily patch status report completed. $HOSTS_NEEDING_PATCHES host(s) require updates." \
                "$LATEST_REPORT"

            return 0
        fi
    else
        log "ERROR: Patch status report failed"
        return 1
    fi
}

# Step 3: Automatic Patching (if enabled)
run_automatic_patching() {
    if [ "$AUTO_PATCH_ENABLED" != "true" ]; then
        log "========================================="
        log "Step 3: Automatic Patching (DISABLED)"
        log "========================================="
        log "Set AUTO_PATCH_ENABLED=true to enable automatic patching"
        return 0
    fi

    log "========================================="
    log "Step 3: Running Automatic Patching"
    log "========================================="

    cd "$ANSIBLE_DIR"

    # Run patching playbook
    ansible-playbook \
        -i inventories/homelab.yml \
        playbooks/quick_patch_all.yml \
        --limit '!truenas' \
        2>&1 | tee -a "$AUTOMATION_LOG"

    local exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        log "Automatic patching completed successfully"

        send_notification \
            "Homelab Automatic Patching Completed" \
            "Daily automatic patching completed successfully. Check logs for details." \
            "$AUTOMATION_LOG"

        return 0
    else
        log "ERROR: Automatic patching failed with exit code $exit_code"

        send_notification \
            "Homelab Automatic Patching FAILED" \
            "Daily automatic patching failed. Manual intervention may be required." \
            "$AUTOMATION_LOG"

        return 1
    fi
}

# Step 4: Cleanup old reports
cleanup_old_reports() {
    log "========================================="
    log "Step 4: Cleaning up old reports"
    log "========================================="

    # Keep last 30 days of reports
    find "$REPORT_DIR" -name "*.html" -type f -mtime +30 -delete 2>&1 | tee -a "$AUTOMATION_LOG"
    find "$REPORT_DIR" -name "*.txt" -type f -mtime +30 -delete 2>&1 | tee -a "$AUTOMATION_LOG"
    find "$LOG_DIR" -name "*.log" -type f -mtime +90 -delete 2>&1 | tee -a "$AUTOMATION_LOG"

    log "Cleanup completed"
}

# Main execution
main() {
    log "========================================="
    log "Ansible Daily Automation - Started"
    log "========================================="

    local start_time=$(date +%s)
    local overall_status=0

    # Step 1: Asset Discovery
    if ! run_asset_discovery; then
        overall_status=1
    fi

    # Step 2: Patch Status Report (always run)
    if ! run_patch_status_report; then
        overall_status=1
    fi

    # Step 3: Automatic Patching (if enabled)
    if ! run_automatic_patching; then
        overall_status=1
    fi

    # Step 4: Cleanup
    cleanup_old_reports

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_minutes=$((duration / 60))

    log "========================================="
    log "Ansible Daily Automation - Completed"
    log "Duration: ${duration_minutes} minutes"
    log "Status: $([ $overall_status -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')"
    log "========================================="

    exit $overall_status
}

# Run main function
main "$@"
