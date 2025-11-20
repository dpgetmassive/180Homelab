# Corosync QDevice Configuration

Quick reference for the Proxmox cluster quorum device setup in 180 Homelab.

## Overview

Two-node Proxmox cluster "springfield" with external QNetd server providing tie-breaker vote for quorum.

## Infrastructure

### Cluster Nodes
- **pve-itchy** (10.16.1.8) - Node ID 1
- **pve-scratchy** (10.16.1.22) - Node ID 3

### QNetd Server
- **n100uck** (10.16.1.18:5403)
- Service: `corosync-qnetd`
- User: `coroqnetd`
- TLS: Enabled with client certificate authentication

## Configuration

### Quorum Setup
- **Algorithm**: Fifty-Fifty split
- **Tie-breaker**: Node with lowest node ID
- **Total votes**: 3 (1 per node + 1 qdevice)
- **Quorum required**: 2 votes

### Certificate Infrastructure
- **CA**: QNet CA
- **Server Cert**: Qnetd Server
- **Client Cert**: springfield cluster certificate
- **Location**: `/etc/corosync/qnetd/nssdb/` (server), `/etc/corosync/qdevice/net/nssdb/` (clients)

## Status Commands

### QNetd Server (10.16.1.18)
```bash
# Service status
systemctl status corosync-qnetd

# Connected clients
corosync-qnetd-tool -s
corosync-qnetd-tool -l

# View logs
journalctl -u corosync-qnetd -f
```

### Cluster Nodes
```bash
# Qdevice status
corosync-qdevice-tool -s
systemctl status corosync-qdevice

# Cluster quorum status
pvecm status

# Corosync status
systemctl status corosync
```

## Troubleshooting

### Certificate Issues

If SSL peer verification fails:

1. **Import cluster certificate on QNetd server**:
   ```bash
   certutil -A -d /etc/corosync/qnetd/nssdb -n "Cluster springfield" -t "P,," -i /etc/corosync/qnetd/nssdb/cluster-springfield.crt
   ```

2. **Fix NSS database permissions**:
   ```bash
   chown -R coroqnetd:coroqnetd /etc/corosync/qnetd/nssdb
   ```

3. **Restart service**:
   ```bash
   systemctl restart corosync-qnetd
   ```

### Verify Certificates
```bash
# List certificates in NSS database
certutil -L -d /etc/corosync/qnetd/nssdb

# View specific certificate
certutil -L -d /etc/corosync/qnetd/nssdb -n "QNet CA"
```

## Expected Output

### Healthy QNetd Server
```
Connected clients:    2
Connected clusters:   1
```

### Healthy Cluster Node
```
State:          Connected
Quorate:        Yes
Total votes:    3
Quorum:         2
```

## Files

### QNetd Server
- Config: `/etc/corosync/qnetd/` (no config file by default)
- NSS DB: `/etc/corosync/qnetd/nssdb/`
- Certificates: `cert9.db`, `key4.db`

### Cluster Nodes
- Config: `/etc/corosync/corosync.conf`
- NSS DB: `/etc/corosync/qdevice/net/nssdb/`

## References

- Cluster name: `springfield`
- Service port: `5403`
- Link mode: `passive`
- IP version: `ipv4-6`
