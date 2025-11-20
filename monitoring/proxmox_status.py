#!/usr/bin/env python3
# save as proxmox_status.py

from flask import Flask, render_template_string, jsonify
import subprocess
import requests
import json
from datetime import datetime

app = Flask(__name__)

NTFY_TOPIC = 'gmdojo-monitoring'
BACKUP_LOG_PATH = '/var/log/proxmox-backup-orchestration.log'
BACKUP_HOST = '10.16.1.22'

NODES = {
    'pve-scratchy': {
        'ip': '10.16.1.22',
        'ssh_alias': 'scratchy',
        'checks': [
            ('Workloads', 'echo "$(qm list | tail -n +2 | wc -l) VMs | $(pct list | tail -n +2 | wc -l) CTs"'),
            ('Hardware', 'echo "$(nproc) cores | $(free -g | grep Mem | awk \'{print $2}\')GB RAM | $(df -h / | tail -1 | awk \'{print $4}\') free"'),
            ('Updates', 'echo "$(apt list --upgradable 2>/dev/null | grep -v Listing | wc -l) total ($(apt list --upgradable 2>/dev/null | grep -i security | wc -l) security)"'),
            ('Uptime', 'uptime -p'),
            ('Cluster Status', 'pvecm status | grep "Quorum information" | wc -l'),
        ],
        'gauges': [
            ('Memory', 'free | grep Mem | awk \'{printf "%.0f,%.0f", ($3/$2)*100, $2/1024/1024}\''),
            ('Root FS', 'df / | tail -1 | awk \'{print $5","$2}\''),
            ('Load', 'uptime | awk -F"load average:" \'{print $2}\' | awk \'{print $1}\' | tr -d \',\''),
        ],
        'logs': [
            ('Backup Log', '/var/log/proxmox-backup-orchestration.log'),
            ('System Log', '/var/log/syslog'),
            ('Task Log', '/var/log/pve/tasks/active'),
        ]
    },
    'pve-itchy': {
        'ip': '10.16.1.8',
        'ssh_alias': 'itchy',
        'checks': [
            ('Workloads', 'echo "$(qm list | tail -n +2 | wc -l) VMs | $(pct list | tail -n +2 | wc -l) CTs"'),
            ('Hardware', 'echo "$(nproc) cores | $(free -g | grep Mem | awk \'{print $2}\')GB RAM | $(df -h / | tail -1 | awk \'{print $4}\') free"'),
            ('Updates', 'echo "$(apt list --upgradable 2>/dev/null | grep -v Listing | wc -l) total ($(apt list --upgradable 2>/dev/null | grep -i security | wc -l) security)"'),
            ('Uptime', 'uptime -p'),
            ('Cluster Status', 'pvecm status | grep "Quorum information" | wc -l'),
        ],
        'gauges': [
            ('Memory', 'free | grep Mem | awk \'{printf "%.0f,%.0f", ($3/$2)*100, $2/1024/1024}\''),
            ('Root FS', 'df / | tail -1 | awk \'{print $5","$2}\''),
            ('Load', 'uptime | awk -F"load average:" \'{print $2}\' | awk \'{print $1}\' | tr -d \',\''),
        ],
        'logs': [
            ('System Log', '/var/log/syslog'),
            ('Task Log', '/var/log/pve/tasks/active'),
        ]
    }
}

# TrueNAS replication checks
TRUENAS_PRIMARY = '10.16.1.6'
REPLICATION_TASKS = [
    {
        'name': 'FileServer → DR',
        'dataset': 'Tank/FileServer',
        'task_id': 4
    },
    {
        'name': 'Downloads → DR',
        'dataset': 'Tank/Downloads',
        'task_id': 5
    }
]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proxmox Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', sans-serif;
            background: #0d1117;
            padding: 20px;
            min-height: 100vh;
            color: #c9d1d9;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            margin-bottom: 30px;
        }

        .banner-container {
            text-align: center;
            margin-bottom: 20px;
            width: 100%;
        }

        .ascii-banner {
            font-family: 'Courier New', 'Monaco', monospace;
            font-size: 10px;
            line-height: 1.2;
            color: #3fb950;
            margin: 0 auto;
            padding: 20px;
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 6px;
            display: inline-block;
            text-align: left;
        }

        .ascii-banner::-webkit-scrollbar {
            height: 6px;
        }

        .ascii-banner::-webkit-scrollbar-track {
            background: #0d1117;
        }

        .ascii-banner::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 3px;
        }

        .header-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 1.3em;
            color: #c9d1d9;
            font-weight: 600;
        }

        .quick-stats {
            display: flex;
            gap: 30px;
            background: #161b22;
            padding: 20px 30px;
            border-radius: 8px;
            border: 1px solid #30363d;
            margin-bottom: 20px;
        }

        .stat-item {
            text-align: center;
        }

        .stat-label {
            font-size: 0.9em;
            color: #8b949e;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 2em;
            font-weight: 600;
        }

        .stat-value.up {
            color: #3fb950;
        }

        .stat-value.down {
            color: #f85149;
        }

        .stat-value.warning {
            color: #d29922;
        }
        
        .node-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .node-card {
            background: #161b22;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #30363d;
            transition: border-color 0.2s;
        }

        .node-card:hover {
            border-color: #8b949e;
        }

        .node-card.online {
            border-left: 4px solid #3fb950;
        }

        .node-card.offline {
            border-left: 4px solid #f85149;
        }
        
        .node-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .node-name {
            font-size: 1.4em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #c9d1d9;
            margin-bottom: 5px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.up {
            background: #238636;
            color: #ffffff;
        }

        .status-badge.down {
            background: #da3633;
            color: #ffffff;
        }

        .node-ip {
            color: #8b949e;
            font-size: 0.9em;
        }
        
        .metrics {
            display: grid;
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #21262d;
        }

        .metric-row:last-child {
            border-bottom: none;
        }

        .metric-row.security-alert {
            background: rgba(218, 54, 51, 0.1);
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #da3633;
            margin-bottom: 8px;
        }

        .metric-label {
            color: #8b949e;
            font-size: 0.9em;
        }

        .metric-row.security-alert .metric-label {
            color: #ff7b72;
            font-weight: 600;
        }

        .metric-value {
            font-weight: 600;
            color: #c9d1d9;
            font-size: 0.9em;
        }

        .metric-row.security-alert .metric-value {
            color: #ff7b72;
        }

        .gauges-section {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #21262d;
        }

        .gauge-title {
            font-size: 0.85em;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 15px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .gauge-container {
            margin-bottom: 15px;
        }

        .gauge-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 0.9em;
        }

        .gauge-label span:first-child {
            color: #c9d1d9;
            font-weight: 500;
        }

        .gauge-label span:last-child {
            color: #8b949e;
            font-size: 0.85em;
        }

        .gauge-bar {
            height: 8px;
            background: #21262d;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }

        .gauge-fill {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 4px;
        }

        .gauge-fill.low {
            background: #3fb950;
        }

        .gauge-fill.medium {
            background: #d29922;
        }

        .gauge-fill.high {
            background: #f85149;
        }

        .top-consumer {
            margin-top: 10px;
            padding: 10px;
            background: #0d1117;
            border: 1px solid #21262d;
            border-radius: 4px;
            font-size: 0.85em;
            color: #8b949e;
        }

        .top-consumer strong {
            color: #c9d1d9;
        }

        .logs-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #21262d;
        }

        .logs-title {
            font-size: 0.85em;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 10px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .log-links {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .log-link {
            background: #21262d;
            color: #58a6ff;
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.85em;
            transition: all 0.2s;
            border: 1px solid #30363d;
        }

        .log-link:hover {
            background: #30363d;
            border-color: #58a6ff;
        }

        .ssh-command {
            background: #21262d;
            color: #58a6ff;
            padding: 6px 12px;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.85em;
            cursor: pointer;
            display: inline-block;
            border: 1px solid #30363d;
            transition: all 0.2s;
        }

        .ssh-command:hover {
            background: #30363d;
            border-color: #58a6ff;
        }
        
        .replication-section {
            background: #161b22;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        .replication-section h2 {
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #c9d1d9;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .replication-grid {
            display: grid;
            gap: 15px;
        }
        
        .replication-item {
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #30363d;
            background: #0d1117;
        }

        .replication-item.success {
            border-left: 3px solid #3fb950;
        }

        .replication-item.error {
            border-left: 3px solid #f85149;
        }

        .replication-item.running {
            border-left: 3px solid #d29922;
        }
        
        .replication-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .replication-name {
            font-weight: 600;
            font-size: 1em;
            color: #c9d1d9;
        }

        .replication-status {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .replication-status.success {
            background: #238636;
            color: #ffffff;
        }

        .replication-status.error {
            background: #da3633;
            color: #ffffff;
        }

        .replication-status.running {
            background: #9e6a03;
            color: #ffffff;
        }

        .replication-details {
            color: #8b949e;
            font-size: 0.85em;
        }

        .replication-details div {
            margin: 5px 0;
        }

        .replication-details strong {
            color: #c9d1d9;
        }
        
        .alerts-section {
            background: #161b22;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        .alerts-section h2 {
            color: #c9d1d9;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: 600;
        }

        .alert-item {
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border: 1px solid #30363d;
            background: #0d1117;
        }

        .alert-item.resolved {
            border-left: 3px solid #3fb950;
        }

        .alert-item.warning {
            border-left: 3px solid #d29922;
        }

        .alert-item.critical {
            border-left: 3px solid #f85149;
        }

        .alert-item.info {
            border-left: 3px solid #58a6ff;
        }

        .alert-title {
            font-weight: 600;
            margin-bottom: 5px;
            color: #c9d1d9;
            font-size: 0.95em;
        }

        .alert-message {
            color: #8b949e;
            font-size: 0.85em;
            margin-bottom: 5px;
        }

        .alert-time {
            color: #6e7681;
            font-size: 0.8em;
        }

        .loading {
            text-align: center;
            padding: 20px;
            color: #8b949e;
            font-size: 0.9em;
        }

        .refresh-info {
            text-align: center;
            color: #6e7681;
            margin-top: 20px;
            padding-bottom: 20px;
            font-size: 0.85em;
        }

        .backup-stale {
            animation: blink-red 1.5s infinite;
        }

        @keyframes blink-red {
            0%, 100% { color: #f85149; }
            50% { color: #ff0000; opacity: 0.7; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="banner-container">
<pre class="ascii-banner">    ______     __     __  ___                _               ____          _
  / ____/__  / /_   /  |/  /___ ___________(_)   _____     / __ \\____    (_)___
 / / __/ _ \\/ __/  / /|_/ / __ `/ ___/ ___/ / | / / _ \\   / / / / __ \\  / / __ \\
/ /_/ /  __/ /_   / /  / / /_/ (__  |__  ) /| |/ /  __/  / /_/ / /_/ / / / /_/ /
\\____/\\___/\\__/  /_/  /_/\\__,_/____/____/_/ |___/\\___/  /_____/\\____/_/ /\\____/
                                                                   /___/        </pre>
            </div>
            <div class="header-info">
                <h1>Infrastructure Monitor</h1>
                <div style="color: #8b949e; font-size: 0.9em;">
                    Last updated: <span id="last-update">-</span>
                </div>
            </div>
        </div>

        <div class="quick-stats" id="quick-stats">
            <div class="stat-item">
                <div class="stat-label">Up</div>
                <div class="stat-value up" id="stat-up">0</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Down</div>
                <div class="stat-value down" id="stat-down">0</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Warnings</div>
                <div class="stat-value warning" id="stat-warnings">0</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Last Backup</div>
                <div class="stat-value" id="stat-backup" style="font-size: 0.8em;">-</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">ZFS Replication</div>
                <div class="stat-value" id="stat-replication" style="font-size: 0.8em;">-</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">CloudSync</div>
                <div class="stat-value" id="stat-cloudsync" style="font-size: 0.8em;">-</div>
            </div>
        </div>
        
        <div class="node-grid" id="nodes-container">
            <div class="loading">Loading node status...</div>
        </div>
        
        <div class="alerts-section">
            <h2>📋 Recent Notifications</h2>
            <div id="alerts-container">
                <div class="loading">Loading notifications...</div>
            </div>
        </div>
        
        <div class="replication-section">
            <h2>🔄 ZFS Replication Status (10.16.1.6 → 10.16.1.20)</h2>
            <div class="replication-grid" id="replication-container">
                <div class="loading">Loading replication status...</div>
            </div>
        </div>

        <div class="replication-section">
            <h2>☁️ Backblaze CloudSync Status</h2>
            <div class="replication-grid" id="cloudsync-container">
                <div class="loading">Loading CloudSync status...</div>
            </div>
        </div>

        <div class="refresh-info">
            Auto-refreshing every 30 seconds
        </div>
    </div>
    
    <script>
        function formatTimeAgo(timestamp) {
            const now = Date.now() / 1000;
            const diff = now - timestamp;
            
            if (diff < 60) return 'Just now';
            if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
            if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
            return Math.floor(diff / 86400) + 'd ago';
        }
        
        function getAlertClass(notification) {
            const title = notification.title.toLowerCase();
            
            if (title.includes('resolved') || title.includes('restored')) {
                return 'resolved';
            } else if (title.includes('critical') || title.includes('unreachable')) {
                return 'critical';
            } else if (title.includes('warning') || title.includes('failed')) {
                return 'warning';
            }
            return 'info';
        }
        
        async function refresh() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Calculate quick stats
                let upCount = 0;
                let downCount = 0;
                let warningCount = 0;

                Object.entries(data.nodes).forEach(([name, node]) => {
                    if (node.reachable) {
                        upCount++;
                        // Check for warnings in metrics (now an array)
                        if (node.metrics) {
                            const securityMetric = node.metrics.find(m => m.label === 'Security Updates');
                            if (securityMetric && parseInt(securityMetric.value) > 0) {
                                warningCount++;
                            }
                        }
                    } else {
                        downCount++;
                    }
                });

                document.getElementById('stat-up').textContent = upCount;
                document.getElementById('stat-down').textContent = downCount;
                document.getElementById('stat-warnings').textContent = warningCount;

                // Update backup status
                const backupElement = document.getElementById('stat-backup');
                if (data.last_backup) {
                    const backupDate = new Date(data.last_backup);
                    const ageHours = data.backup_age_hours || 0;
                    const timeAgo = formatTimeAgo(backupDate.getTime() / 1000);

                    backupElement.textContent = timeAgo;

                    if (ageHours > 24) {
                        backupElement.classList.add('backup-stale');
                        backupElement.classList.remove('up');
                    } else {
                        backupElement.classList.add('up');
                        backupElement.classList.remove('backup-stale');
                    }
                } else {
                    backupElement.textContent = 'Never';
                    backupElement.classList.add('backup-stale');
                    backupElement.classList.remove('up');
                }

                // Update ZFS Replication status
                const replicationElement = document.getElementById('stat-replication');
                if (data.replication && data.replication.length > 0) {
                    const latestRepl = data.replication[0];
                    if (latestRepl.state === 'FINISHED') {
                        replicationElement.textContent = latestRepl.last_run ? formatTimeAgo(new Date(latestRepl.last_run).getTime() / 1000) : 'Success';
                        replicationElement.classList.add('up');
                        replicationElement.classList.remove('backup-stale', 'down', 'warning');
                    } else if (latestRepl.state === 'RUNNING') {
                        replicationElement.textContent = 'Running...';
                        replicationElement.classList.add('warning');
                        replicationElement.classList.remove('up', 'down', 'backup-stale');
                    } else if (latestRepl.state === 'ERROR') {
                        replicationElement.textContent = 'Error';
                        replicationElement.classList.add('down');
                        replicationElement.classList.remove('up', 'backup-stale', 'warning');
                    } else {
                        replicationElement.textContent = latestRepl.last_run ? formatTimeAgo(new Date(latestRepl.last_run).getTime() / 1000) : 'Idle';
                        replicationElement.classList.add('up');
                        replicationElement.classList.remove('down', 'backup-stale', 'warning');
                    }
                } else {
                    replicationElement.textContent = 'N/A';
                    replicationElement.classList.remove('up', 'down', 'backup-stale', 'warning');
                }

                // Update CloudSync status
                const cloudsyncElement = document.getElementById('stat-cloudsync');
                if (data.cloudsync && data.cloudsync.length > 0) {
                    const latestSync = data.cloudsync[0];
                    if (latestSync.state === 'SUCCESS') {
                        cloudsyncElement.textContent = latestSync.last_run ? formatTimeAgo(new Date(latestSync.last_run).getTime() / 1000) : 'Success';
                        cloudsyncElement.classList.add('up');
                        cloudsyncElement.classList.remove('backup-stale', 'down');
                    } else if (latestSync.state === 'RUNNING' || latestSync.state === 'WAITING') {
                        cloudsyncElement.textContent = 'Running...';
                        cloudsyncElement.classList.add('warning');
                        cloudsyncElement.classList.remove('up', 'down', 'backup-stale');
                    } else if (latestSync.state === 'ERROR' || latestSync.state === 'FAILED') {
                        cloudsyncElement.textContent = 'Error';
                        cloudsyncElement.classList.add('down');
                        cloudsyncElement.classList.remove('up', 'backup-stale');
                    } else {
                        cloudsyncElement.textContent = latestSync.last_run ? formatTimeAgo(new Date(latestSync.last_run).getTime() / 1000) : 'Idle';
                        cloudsyncElement.classList.add('up');
                        cloudsyncElement.classList.remove('down', 'backup-stale');
                    }
                } else {
                    cloudsyncElement.textContent = 'N/A';
                    cloudsyncElement.classList.remove('up', 'down', 'backup-stale');
                }

                // Update nodes
                const nodesHTML = Object.entries(data.nodes).map(([name, node]) => {
                    const statusClass = node.reachable ? 'online' : 'offline';
                    const statusText = node.reachable ? 'Up' : 'Down';
                    const badgeClass = node.reachable ? 'up' : 'down';
                    
                    // Render gauges
                    const gaugesHTML = node.gauges ? `
                        <div class="gauges-section">
                            <div class="gauge-title">Resource Utilization</div>
                            ${Object.entries(node.gauges).map(([label, value]) => {
                                let percent = 0;
                                let displayValue = value;
                                let gaugeClass = 'low';

                                if (label === 'Memory') {
                                    const parts = value.split(',');
                                    percent = parseFloat(parts[0]) || 0;
                                    const totalGB = parseFloat(parts[1]) || 0;
                                    displayValue = `${percent.toFixed(1)}% (${totalGB.toFixed(1)}GB total)`;
                                } else if (label === 'Root FS') {
                                    const parts = value.split(',');
                                    percent = parseFloat(parts[0].replace('%', '')) || 0;
                                    displayValue = `${percent.toFixed(1)}%`;
                                } else if (label === 'Load') {
                                    const loadVal = parseFloat(value) || 0;
                                    // Assuming 8 cores, normalize load (adjust based on your CPU count)
                                    const cpuCount = 8;
                                    percent = Math.min((loadVal / cpuCount) * 100, 100);
                                    displayValue = value;
                                }

                                if (percent >= 90) gaugeClass = 'high';
                                else if (percent >= 80) gaugeClass = 'medium';

                                return `
                                    <div class="gauge-container">
                                        <div class="gauge-label">
                                            <span>${label}</span>
                                            <span>${displayValue}</span>
                                        </div>
                                        <div class="gauge-bar">
                                            <div class="gauge-fill ${gaugeClass}" style="width: ${percent}%"></div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                            ${node.top_consumer ? `<div class="top-consumer"><strong>Top CPU Consumer:</strong> ${node.top_consumer}</div>` : ''}
                        </div>
                    ` : '';

                    const metricsHTML = node.metrics ?
                        node.metrics.map((metric) => {
                            // Check if this is security updates and value > 0
                            const isSecurityAlert = metric.label === 'Security Updates' && parseInt(metric.value) > 0;
                            const rowClass = isSecurityAlert ? 'metric-row security-alert' : 'metric-row';

                            return `
                                <div class="${rowClass}">
                                    <span class="metric-label">${metric.label}</span>
                                    <span class="metric-value">${metric.value}</span>
                                </div>
                            `;
                        }).join('') :
                        '<div class="loading">Fetching metrics...</div>';

                    const logsHTML = node.logs ? `
                        <div class="logs-section">
                            <div class="logs-title">📄 Quick Log Access</div>
                            <div class="log-links">
                                ${node.logs.map(log => `
                                    <a href="#" class="log-link" 
                                       onclick="copyLogCommand('${node.ssh_alias}', '${log.path}'); return false;">
                                        ${log.name}
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    ` : '';
                    
                    return `
                        <div class="node-card ${statusClass}">
                            <div class="node-header">
                                <div>
                                    <div class="node-name">
                                        ${name}
                                        <span class="status-badge ${badgeClass}">${statusText}</span>
                                    </div>
                                    <div class="node-ip">${node.ip}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="ssh-command" onclick="copyToClipboard('ssh ${node.ssh_alias}')">
                                        ssh ${node.ssh_alias}
                                    </div>
                                </div>
                            </div>
                            ${gaugesHTML}
                            <div class="metrics">
                                ${metricsHTML}
                            </div>
                            ${logsHTML}
                        </div>
                    `;
                }).join('');
                
                document.getElementById('nodes-container').innerHTML = nodesHTML;
                
                // Update alerts
                if (!data.notifications) {
                    document.getElementById('alerts-container').innerHTML =
                        '<div class="loading" style="color: #f85149;">Failed to load notifications from ntfy</div>';
                } else if (data.notifications && data.notifications.length > 0) {
                    // Build a map of resolved issues
                    const resolvedIssues = new Set();
                    data.notifications.forEach(notif => {
                        if (notif.title.toLowerCase().includes('resolved') ||
                            notif.title.toLowerCase().includes('restored')) {
                            // Extract the issue type (e.g., "Storage", "Cluster")
                            const match = notif.title.match(/\\[(.*?)\\]\\s+(\\w+)\\s+(Resolved|Restored)/);
                            if (match) {
                                const node = match[1];
                                const issueType = match[2];
                                resolvedIssues.add(`${node}:${issueType}`);
                            }
                        }
                    });

                    const alertsHTML = data.notifications.slice(0, 15).map(notif => {
                        let alertClass = getAlertClass(notif);
                        let resolvedStamp = '';

                        // Check if this alert has been resolved
                        const titleMatch = notif.title.match(/\\[(.*?)\\]\\s+(\\w+)/);
                        if (titleMatch) {
                            const node = titleMatch[1];
                            const issueType = titleMatch[2];
                            const issueKey = `${node}:${issueType}`;

                            if (resolvedIssues.has(issueKey) &&
                                !notif.title.toLowerCase().includes('resolved') &&
                                !notif.title.toLowerCase().includes('restored')) {
                                alertClass = 'resolved';
                                resolvedStamp = '<span style="color: #00ff41; font-weight: bold;"> [RESOLVED]</span>';
                            }
                        }

                        return `
                            <div class="alert-item ${alertClass}">
                                <div class="alert-title">${notif.title}${resolvedStamp}</div>
                                <div class="alert-message">${notif.message}</div>
                                <div class="alert-time">${formatTimeAgo(notif.time)}</div>
                            </div>
                        `;
                    }).join('');
                    document.getElementById('alerts-container').innerHTML = alertsHTML;
                } else {
                    document.getElementById('alerts-container').innerHTML =
                        '<div class="loading">No recent notifications</div>';
                }
                
                // Update replication status
                if (!data.replication || data.replication.length === 0) {
                    document.getElementById('replication-container').innerHTML =
                        '<div class="loading" style="color: #f85149;">Failed to load replication status from TrueNAS</div>';
                } else if (data.replication) {
                    const replHTML = data.replication.map(repl => {
                        let statusClass = 'success';
                        let statusText = 'FINISHED';
                        
                        if (repl.state === 'ERROR') {
                            statusClass = 'error';
                            statusText = 'ERROR';
                        } else if (repl.state === 'RUNNING') {
                            statusClass = 'running';
                            statusText = 'RUNNING';
                        }
                        
                        return `
                            <div class="replication-item ${statusClass}">
                                <div class="replication-header">
                                    <div class="replication-name">${repl.name}</div>
                                    <div class="replication-status ${statusClass}">${statusText}</div>
                                </div>
                                <div class="replication-details">
                                    <div><strong>Dataset:</strong> ${repl.dataset}</div>
                                    ${repl.last_snapshot ? `<div><strong>Last Snapshot:</strong> ${repl.last_snapshot}</div>` : ''}
                                    ${repl.last_run ? `<div><strong>Last Run:</strong> ${repl.last_run}</div>` : ''}
                                    ${repl.error ? `<div style="color: #dc2626;"><strong>Error:</strong> ${repl.error}</div>` : ''}
                                </div>
                            </div>
                        `;
                    }).join('');
                    document.getElementById('replication-container').innerHTML = replHTML;
                }

                // Update CloudSync status
                if (!data.cloudsync || data.cloudsync.length === 0) {
                    document.getElementById('cloudsync-container').innerHTML =
                        '<div class="loading" style="color: #f85149;">Failed to load CloudSync status from TrueNAS</div>';
                } else if (data.cloudsync) {
                    const cloudHTML = data.cloudsync.map(sync => {
                        let statusClass = 'success';
                        let statusText = 'SUCCESS';

                        if (sync.state === 'ERROR' || sync.state === 'FAILED') {
                            statusClass = 'error';
                            statusText = 'ERROR';
                        } else if (sync.state === 'RUNNING') {
                            statusClass = 'running';
                            statusText = 'RUNNING';
                        } else if (sync.state === 'WAITING') {
                            statusClass = 'running';
                            statusText = 'WAITING';
                        }

                        return `
                            <div class="replication-item ${statusClass}">
                                <div class="replication-header">
                                    <div class="replication-name">${sync.name}</div>
                                    <div class="replication-status ${statusClass}">${statusText}</div>
                                </div>
                                <div class="replication-details">
                                    <div><strong>Source:</strong> ${sync.path}</div>
                                    <div><strong>Destination:</strong> Backblaze B2 (${sync.bucket})</div>
                                    ${sync.last_run ? `<div><strong>Last Run:</strong> ${sync.last_run}</div>` : ''}
                                    ${sync.progress ? `<div><strong>Progress:</strong> ${sync.progress}</div>` : ''}
                                    ${sync.error ? `<div style="color: #dc2626;"><strong>Error:</strong> ${sync.error}</div>` : ''}
                                </div>
                            </div>
                        `;
                    }).join('');
                    document.getElementById('cloudsync-container').innerHTML = cloudHTML;
                }

                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Failed to refresh:', error);
            }
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text);
            showNotification('Copied: ' + text);
        }
        
        function copyLogCommand(host, logPath) {
            const command = `ssh ${host} "tail -f ${logPath}"`;
            navigator.clipboard.writeText(command);
            showNotification('Copied log command!');
        }
        
        function showNotification(message) {
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff8c00;
                color: #1a1a1a;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                z-index: 1000;
                font-weight: bold;
                animation: slideIn 0.3s ease-out;
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, 2000);
        }
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        // Initial load
        refresh();
        
        // Auto-refresh every 30 seconds
        setInterval(refresh, 30000);
    </script>
</body>
</html>
'''

def run_ssh_command(host, command):
    """Run command on remote host via SSH"""
    try:
        result = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=no', 
             f'root@{host}', command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else 'N/A'
    except:
        return 'N/A'

def check_node_connectivity(ip):
    """Check if node is reachable"""
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', ip],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def get_replication_status():
    """Get ZFS replication status from TrueNAS Primary"""
    try:
        result = run_ssh_command(
            TRUENAS_PRIMARY,
            'midclt call replication.query'
        )
        
        if result == 'N/A':
            return []
        
        replication_data = json.loads(result)
        replication_status = []
        
        for task in REPLICATION_TASKS:
            task_data = next((r for r in replication_data if r['id'] == task['task_id']), None)
            
            if task_data:
                status = {
                    'name': task['name'],
                    'dataset': task['dataset'],
                    'state': task_data['state']['state'],
                    'last_snapshot': task_data['state'].get('last_snapshot'),
                    'error': task_data['state'].get('error'),
                    'last_run': None
                }
                
                # Format last run time
                if task_data['state'].get('datetime'):
                    timestamp = task_data['state']['datetime'].get('$date')
                    if timestamp:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        status['last_run'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                replication_status.append(status)
        
        return replication_status
    except Exception as e:
        print(f"Error getting replication status: {e}")
        return []

def get_cloudsync_status():
    """Get Backblaze CloudSync status from TrueNAS Primary"""
    try:
        result = run_ssh_command(
            TRUENAS_PRIMARY,
            'midclt call cloudsync.query'
        )

        if result == 'N/A':
            return []

        cloudsync_data = json.loads(result)
        cloudsync_status = []

        for task in cloudsync_data:
            # Only include enabled tasks
            if not task.get('enabled'):
                continue

            status = {
                'name': task.get('description', 'Unknown'),
                'path': task.get('path', 'N/A'),
                'bucket': task.get('attributes', {}).get('bucket', 'N/A'),
                'direction': task.get('direction', 'PUSH'),
                'state': 'IDLE',
                'last_run': None,
                'transfers': None,
                'progress': None,
                'error': None
            }

            # Get job information if available
            if task.get('job'):
                job = task['job']
                status['state'] = job.get('state', 'UNKNOWN')
                status['error'] = job.get('error')

                # Get progress info
                if job.get('progress'):
                    prog = job['progress']
                    status['progress'] = prog.get('description')
                    status['transfers'] = prog.get('percent')

                # Format last run time
                if job.get('time_finished'):
                    timestamp = job['time_finished'].get('$date')
                    if timestamp:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        status['last_run'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                elif job.get('time_started'):
                    timestamp = job['time_started'].get('$date')
                    if timestamp:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        status['last_run'] = dt.strftime('%Y-%m-%d %H:%M:%S')

            cloudsync_status.append(status)

        return cloudsync_status
    except Exception as e:
        print(f"Error getting CloudSync status: {e}")
        return []

def fetch_ntfy_notifications():
    """Fetch notifications from ntfy"""
    try:
        response = requests.get(
            f'https://ntfy.sh/{NTFY_TOPIC}/json?poll=1&since=24h',
            timeout=15
        )
        if response.status_code != 200:
            print(f"ntfy returned status {response.status_code}")
            return []

        notifications = []
        for line in response.text.strip().split('\n'):
            if line:
                try:
                    notif = json.loads(line)
                    # Some notifications have JSON nested in the message field
                    if notif.get('message') and notif['message'].startswith('{'):
                        try:
                            nested = json.loads(notif['message'])
                            notif['title'] = nested.get('title', notif.get('title', ''))
                            notif['message'] = nested.get('message', '')
                            notif['tags'] = nested.get('tags', notif.get('tags', []))
                        except:
                            pass
                    notifications.append(notif)
                except:
                    pass
        return list(reversed(notifications))
    except Exception as e:
        print(f"Error fetching ntfy notifications: {e}")
        return []

def get_last_backup_timestamp():
    """Get timestamp of last successful backup from log"""
    try:
        # Get last 50 lines of backup log and find the most recent "Backup Cycle Summary"
        result = run_ssh_command(
            BACKUP_HOST,
            f"grep 'Backup Cycle Summary' {BACKUP_LOG_PATH} | tail -1"
        )

        if result == 'N/A' or not result:
            return None

        # Extract timestamp from log line format: [2025-11-20 11:45:30] === Backup Cycle Summary ===
        import re
        match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', result)
        if match:
            timestamp_str = match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            return timestamp

        return None
    except Exception as e:
        print(f"Error getting backup timestamp: {e}")
        return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def get_top_vm_consumer(host):
    """Get the VM/LXC consuming the most CPU"""
    try:
        # Get all VMs/CTs with CPU usage percentage
        result = run_ssh_command(host, 'qm list | tail -n +2 | awk \'{print $1","$2","$3}\'')
        if result == 'N/A' or not result:
            return None

        vms = []
        for line in result.split('\n'):
            if line.strip():
                parts = line.split(',')
                if len(parts) == 3:
                    vmid, name, cpu = parts
                    try:
                        # CPU is shown as percentage (e.g., "0.05" = 5%)
                        cpu_pct = float(cpu) * 100
                        vms.append({'id': vmid, 'name': name, 'cpu': cpu_pct})
                    except:
                        pass

        # Also get containers
        ct_result = run_ssh_command(host, 'pct list | tail -n +2 | awk \'{print $1","$2","$3}\'')
        if ct_result != 'N/A' and ct_result:
            for line in ct_result.split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) == 3:
                        ctid, name, cpu = parts
                        try:
                            cpu_pct = float(cpu) * 100
                            vms.append({'id': f"CT{ctid}", 'name': name, 'cpu': cpu_pct})
                        except:
                            pass

        if vms:
            top_vm = max(vms, key=lambda x: x['cpu'])
            return f"{top_vm['id']} ({top_vm['name']}) - {top_vm['cpu']:.1f}% CPU"

        return None
    except:
        return None

# Track resource alert states to avoid alert spam
resource_alert_states = {}

def check_resource_thresholds(node_name, gauges):
    """Check resource thresholds and send ntfy alerts if needed"""
    global resource_alert_states

    if node_name not in resource_alert_states:
        resource_alert_states[node_name] = {}

    alerts = []

    for resource, value in gauges.items():
        percent = 0
        display_value = value

        # Parse percentage from gauge data
        if resource == 'Memory':
            parts = value.split(',')
            percent = float(parts[0]) if parts else 0
            total_gb = float(parts[1]) if len(parts) > 1 else 0
            display_value = f"{percent:.1f}% ({total_gb:.1f}GB total)"
        elif resource == 'Root FS':
            parts = value.split(',')
            percent = float(parts[0].replace('%', '')) if parts else 0
            display_value = f"{percent:.1f}%"
        elif resource == 'Load':
            load_val = float(value) if value else 0
            cpu_count = 8  # Adjust based on your systems
            percent = min((load_val / cpu_count) * 100, 100)
            display_value = f"{load_val} (normalized: {percent:.1f}%)"

        # Check thresholds (higher thresholds for load during backups)
        current_state = resource_alert_states[node_name].get(resource, 'normal')
        new_state = 'normal'

        # More lenient thresholds for load
        if resource == 'Load':
            if percent >= 150:  # 150% = 12/8 cores = very high load
                new_state = 'critical'
            elif percent >= 125:  # 125% = 10/8 cores = high load
                new_state = 'warning'
        else:
            if percent >= 90:
                new_state = 'critical'
            elif percent >= 80:
                new_state = 'warning'

        # Send alert if state changed to warning or critical
        if new_state != current_state and new_state != 'normal':
            priority = 5 if new_state == 'critical' else 4
            title = f"[{node_name}] {resource} {'Critical' if new_state == 'critical' else 'Warning'}"
            message = f"{resource} is at {display_value}"
            tags = ['chart_with_upwards_trend', 'warning'] if new_state == 'warning' else ['rotating_light', 'fire']

            send_ntfy_alert(title, message, priority, tags)

        # Send resolved alert if state changed from warning/critical to normal
        elif current_state in ['warning', 'critical'] and new_state == 'normal':
            title = f"[{node_name}] {resource} Resolved"
            message = f"{resource} is now at {display_value}"
            send_ntfy_alert(title, message, 3, ['white_check_mark', 'chart_with_downwards_trend'])

        resource_alert_states[node_name][resource] = new_state

def send_ntfy_alert(title, message, priority, tags):
    """Send alert to ntfy"""
    try:
        requests.post(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            json={
                'title': title,
                'message': message,
                'priority': priority,
                'tags': tags
            },
            timeout=5
        )
    except Exception as e:
        print(f"Failed to send ntfy alert: {e}")

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    last_backup = get_last_backup_timestamp()
    backup_age_hours = None
    if last_backup:
        backup_age_hours = (datetime.now() - last_backup).total_seconds() / 3600

    status = {
        'nodes': {},
        'notifications': fetch_ntfy_notifications(),
        'replication': get_replication_status(),
        'cloudsync': get_cloudsync_status(),
        'last_backup': last_backup.isoformat() if last_backup else None,
        'backup_age_hours': backup_age_hours
    }

    for name, config in NODES.items():
        node_status = {
            'ip': config['ip'],
            'ssh_alias': config['ssh_alias'],
            'cpu_cores': config.get('cpu_cores'),
            'memory_gb': config.get('memory_gb'),
            'reachable': check_node_connectivity(config['ip']),
            'metrics': {},
            'gauges': {},
            'top_consumer': None,
            'logs': []
        }

        # If node is reachable, get detailed metrics
        if node_status['reachable']:
            # Use a list to preserve order
            metrics_list = []
            for label, command in config['checks']:
                value = run_ssh_command(config['ip'], command)
                metrics_list.append({'label': label, 'value': value})
            node_status['metrics'] = metrics_list

            # Get gauge data
            if 'gauges' in config:
                for label, command in config['gauges']:
                    result = run_ssh_command(config['ip'], command)
                    node_status['gauges'][label] = result

                # Check resource thresholds and send alerts if needed
                check_resource_thresholds(name, node_status['gauges'])

            # Get top consumer
            node_status['top_consumer'] = get_top_vm_consumer(config['ip'])

            # Add log information
            for log_name, log_path in config['logs']:
                node_status['logs'].append({
                    'name': log_name,
                    'path': log_path
                })

        status['nodes'][name] = node_status

    return jsonify(status)

if __name__ == '__main__':
    print("Starting Proxmox Status Dashboard...")
    print("Open http://localhost:81 in your browser")
    app.run(host='0.0.0.0', port=81, debug=True)


