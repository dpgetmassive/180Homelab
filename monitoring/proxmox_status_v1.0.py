#!/usr/bin/env python3
# save as proxmox_status.py

from flask import Flask, render_template_string, jsonify
import subprocess
import requests
import json
from datetime import datetime

app = Flask(__name__)

NTFY_TOPIC = 'gmdojo-monitoring'

NODES = {
    'pve-scratchy': {
        'ip': '10.16.1.22',
        'ssh_alias': 'scratchy',
        'checks': [
            ('Cluster Status', 'pvecm status | grep "Quorum information" | wc -l'),
            ('VM Count', 'qm list | tail -n +2 | wc -l'),
            ('LXC Count', 'pct list | tail -n +2 | wc -l'),
            ('Storage Used', 'df -h / | tail -1 | awk \'{print $5}\''),
            ('Security Updates', 'apt list --upgradable 2>/dev/null | grep -i security | wc -l'),
            ('Total Updates', 'apt list --upgradable 2>/dev/null | grep -v Listing | wc -l'),
            ('Uptime', 'uptime -p'),
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
            ('Cluster Status', 'pvecm status | grep "Quorum information" | wc -l'),
            ('VM Count', 'qm list | tail -n +2 | wc -l'),
            ('LXC Count', 'pct list | tail -n +2 | wc -l'),
            ('Storage Used', 'df -h / | tail -1 | awk \'{print $5}\''),
            ('Security Updates', 'apt list --upgradable 2>/dev/null | grep -i security | wc -l'),
            ('Total Updates', 'apt list --upgradable 2>/dev/null | grep -v Listing | wc -l'),
            ('Uptime', 'uptime -p'),
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
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'VT323', monospace;
            background: #000000;
            padding: 20px;
            min-height: 100vh;
            color: #00ff41;
            letter-spacing: 0.5px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: #00ff41;
            margin-bottom: 30px;
            padding: 25px;
            background: #000000;
            border-radius: 0;
            border: 2px solid #00ff41;
        }

        .ascii-art {
            font-family: 'Courier New', monospace;
            font-size: 1.2em;
            line-height: 1.2;
            color: #00ff41;
            white-space: pre;
            margin-bottom: 25px;
            letter-spacing: 0.5px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 15px;
            letter-spacing: 2px;
        }

        .header .subtitle {
            color: #00ff41;
            font-size: 1.2em;
        }
        
        .node-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .node-card {
            background: #000000;
            border-radius: 0;
            padding: 25px;
            border: 2px solid #00ff41;
        }

        .node-card.online {
            border: 2px solid #00ff41;
        }

        .node-card.offline {
            border: 2px solid #ff0000;
        }
        
        .node-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .node-name {
            font-size: 1.8em;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #00ff41;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-dot.online {
            background: #00ff41;
        }

        .status-dot.offline {
            background: #ff0000;
        }

        .node-ip {
            color: #00ff41;
            font-size: 1.1em;
        }
        
        .metrics {
            display: grid;
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            background: #000000;
            border-radius: 0;
            border: 1px solid #00ff41;
        }

        .metric-row.security-alert {
            background: #000000;
            border: 2px solid #ff0000;
        }

        .metric-label {
            color: #00ff41;
            font-weight: 500;
            font-size: 1.1em;
        }

        .metric-row.security-alert .metric-label {
            color: #ff0000;
            font-weight: bold;
        }

        .metric-value {
            font-weight: bold;
            color: #00ff41;
            font-size: 1.1em;
        }

        .metric-row.security-alert .metric-value {
            color: #ff0000;
            font-weight: bold;
        }

        .gauges-section {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #00ff41;
        }

        .gauge-title {
            font-size: 1.1em;
            color: #00ff41;
            text-transform: uppercase;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .gauge-container {
            margin-bottom: 12px;
        }

        .gauge-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 1em;
            color: #00ff41;
        }

        .gauge-bar {
            height: 20px;
            background: #000000;
            border: 1px solid #00ff41;
            position: relative;
            overflow: hidden;
        }

        .gauge-fill {
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85em;
            font-weight: bold;
        }

        .gauge-fill.low {
            background: #00ff41;
            color: #000000;
        }

        .gauge-fill.medium {
            background: #ffff00;
            color: #000000;
        }

        .gauge-fill.high {
            background: #ff0000;
            color: #000000;
        }

        .top-consumer {
            margin-top: 10px;
            padding: 8px;
            background: #000000;
            border: 1px solid #00ff41;
            font-size: 0.9em;
            color: #00ff41;
        }

        .top-consumer strong {
            color: #00ff41;
        }

        .logs-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px solid #00ff41;
        }

        .logs-title {
            font-size: 1.1em;
            color: #00ff41;
            text-transform: uppercase;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .log-links {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .log-link {
            background: #000000;
            color: #00ff41;
            padding: 8px 14px;
            border-radius: 0;
            text-decoration: none;
            font-size: 1em;
            transition: all 0.2s;
            border: 1px solid #00ff41;
        }

        .log-link:hover {
            background: #00ff41;
            color: #000000;
        }

        .ssh-command {
            background: #000000;
            color: #00ff41;
            padding: 8px 12px;
            border-radius: 0;
            font-family: 'VT323', monospace;
            font-size: 1.1em;
            cursor: pointer;
            display: inline-block;
            border: 2px solid #00ff41;
            transition: all 0.2s;
        }

        .ssh-command:hover {
            background: #00ff41;
            color: #000000;
        }
        
        .replication-section {
            background: #000000;
            border-radius: 0;
            padding: 25px;
            margin-bottom: 30px;
            border: 2px solid #00ff41;
        }

        .replication-section h2 {
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #00ff41;
            font-size: 1.8em;
        }
        
        .replication-grid {
            display: grid;
            gap: 15px;
        }
        
        .replication-item {
            padding: 15px;
            border-radius: 0;
            border: 1px solid #00ff41;
            background: #000000;
        }

        .replication-item.success {
            border-color: #00ff41;
            background: #000000;
        }

        .replication-item.error {
            border-color: #ff0000;
            background: #000000;
        }

        .replication-item.running {
            border-color: #ffff00;
            background: #000000;
        }
        
        .replication-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .replication-name {
            font-weight: bold;
            font-size: 1.3em;
            color: #00ff41;
        }

        .replication-status {
            padding: 6px 12px;
            border-radius: 0;
            font-size: 1em;
            font-weight: 600;
            border: 1px solid;
        }

        .replication-status.success {
            background: #00ff41;
            color: #000000;
            border-color: #00ff41;
        }

        .replication-status.error {
            background: #ff0000;
            color: #000000;
            border-color: #ff0000;
        }

        .replication-status.running {
            background: #ffff00;
            color: #000000;
            border-color: #ffff00;
        }

        .replication-details {
            color: #00ff41;
            font-size: 1em;
        }

        .replication-details div {
            margin: 5px 0;
        }

        .replication-details strong {
            color: #00ff41;
        }
        
        .alerts-section {
            background: #000000;
            border-radius: 0;
            padding: 25px;
            margin-bottom: 20px;
            border: 2px solid #00ff41;
        }

        .alerts-section h2 {
            color: #00ff41;
            margin-bottom: 20px;
            font-size: 1.8em;
        }

        .alert-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 0;
            border: 1px solid #00ff41;
            background: #000000;
        }

        .alert-item.resolved {
            background: #000000;
            border-color: #00ff41;
        }

        .alert-item.warning {
            background: #000000;
            border-color: #ffff00;
        }

        .alert-item.critical {
            background: #000000;
            border-color: #ff0000;
        }

        .alert-item.info {
            background: #000000;
            border-color: #00ff41;
        }

        .alert-title {
            font-weight: bold;
            margin-bottom: 5px;
            color: #00ff41;
            font-size: 1.2em;
        }

        .alert-message {
            color: #00ff41;
            font-size: 1em;
            margin-bottom: 5px;
        }

        .alert-time {
            color: #00ff41;
            font-size: 0.95em;
        }

        .loading {
            text-align: center;
            padding: 20px;
            color: #00ff41;
            font-size: 1.2em;
        }

        .refresh-info {
            text-align: center;
            color: #00ff41;
            margin-top: 20px;
            padding-bottom: 20px;
            font-size: 1.1em;
        }

        .refresh-info span {
            color: #00ff41;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="ascii-art">
 ┌─┐┌─┐┌┬┐  ┌┬┐┌─┐┌─┐┌─┐┬┬  ┬┌─┐  ┌┬┐┌─┐ ┬┌─┐
 │ ┬├┤  │   │││├─┤└─┐└─┐│└┐┌┘├┤    │││ │ ││ │
 └─┘└─┘ ┴   ┴ ┴┴ ┴└─┘└─┘┴ └┘ └─┘  ─┴┘└─┘└┘└─┘
            </div>
            <h1>PROXMOX INFRASTRUCTURE MONITOR</h1>
            <div class="subtitle">Real-time monitoring • Last updated: <span id="last-update">-</span></div>
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
                
                // Update nodes
                const nodesHTML = Object.entries(data.nodes).map(([name, node]) => {
                    const statusClass = node.reachable ? 'online' : 'offline';
                    const statusText = node.reachable ? 'Online' : 'Offline';
                    
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
                            ${node.top_consumer ? `<div class="top-consumer"><strong>Top Consumer:</strong> ${node.top_consumer}</div>` : ''}
                        </div>
                    ` : '';

                    const metricsHTML = node.metrics ?
                        Object.entries(node.metrics).map(([label, value]) => {
                            // Check if this is security updates and value > 0
                            const isSecurityAlert = label === 'Security Updates' && parseInt(value) > 0;
                            const rowClass = isSecurityAlert ? 'metric-row security-alert' : 'metric-row';

                            return `
                                <div class="${rowClass}">
                                    <span class="metric-label">${label}</span>
                                    <span class="metric-value">${value}</span>
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
                                        <span class="status-dot ${statusClass}"></span>
                                        ${name}
                                    </div>
                                    <div class="node-ip">${node.ip}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-weight: bold; color: ${node.reachable ? '#00ff41' : '#ff0000'}; margin-bottom: 8px; font-size: 1.2em;">
                                        ${statusText}
                                    </div>
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
                if (data.notifications && data.notifications.length > 0) {
                    // Build a map of resolved issues
                    const resolvedIssues = new Set();
                    data.notifications.forEach(notif => {
                        if (notif.title.toLowerCase().includes('resolved') ||
                            notif.title.toLowerCase().includes('restored')) {
                            // Extract the issue type (e.g., "Storage", "Cluster")
                            const match = notif.title.match(/\[(.*?)\]\s+(\w+)\s+(Resolved|Restored)/);
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
                        const titleMatch = notif.title.match(/\[(.*?)\]\s+(\w+)/);
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
                if (data.replication) {
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

def fetch_ntfy_notifications():
    """Fetch notifications from ntfy"""
    try:
        response = requests.get(
            f'https://ntfy.sh/{NTFY_TOPIC}/json?poll=1&since=24h',
            timeout=10
        )
        notifications = []
        for line in response.text.strip().split('\n'):
            if line:
                notifications.append(json.loads(line))
        return list(reversed(notifications))
    except:
        return []

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def get_top_vm_consumer(host):
    """Get the VM/LXC consuming the most resources"""
    try:
        # Get all VMs with memory usage
        result = run_ssh_command(host, 'qm list | tail -n +2 | awk \'{print $1","$2","$4}\'')
        if result == 'N/A' or not result:
            return None

        vms = []
        for line in result.split('\n'):
            if line.strip():
                parts = line.split(',')
                if len(parts) == 3:
                    vmid, name, mem = parts
                    try:
                        vms.append({'id': vmid, 'name': name, 'mem': int(mem)})
                    except:
                        pass

        if vms:
            top_vm = max(vms, key=lambda x: x['mem'])
            return f"VM {top_vm['id']} ({top_vm['name']}) - {top_vm['mem']}MB"

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

        # Check thresholds
        current_state = resource_alert_states[node_name].get(resource, 'normal')
        new_state = 'normal'

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
    status = {
        'nodes': {},
        'notifications': fetch_ntfy_notifications(),
        'replication': get_replication_status()
    }

    for name, config in NODES.items():
        node_status = {
            'ip': config['ip'],
            'ssh_alias': config['ssh_alias'],
            'reachable': check_node_connectivity(config['ip']),
            'metrics': {},
            'gauges': {},
            'top_consumer': None,
            'logs': []
        }

        # If node is reachable, get detailed metrics
        if node_status['reachable']:
            for label, command in config['checks']:
                node_status['metrics'][label] = run_ssh_command(config['ip'], command)

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


