# Infrastructure Rebuild Plan

Complete documentation needed to rebuild the homelab from scratch (excluding data).

**Goal**: Pull a fresh Proxmox server out of the box and rebuild entire environment from Git.

**Last Updated:** 2025-11-10

---

## Current State Analysis

### What We Have Documented ✅
- [x] Ansible inventory (all 17 hosts)
- [x] Network topology and DNS architecture
- [x] Service catalog with URLs
- [x] Docker infrastructure (Traefik, Portainer, etc.)
- [x] How to add new services guide
- [x] SSH key structure

### What's Missing ❌

## 1. Proxmox Host Configuration

### 1.1 Base Proxmox Installation
**Status**: ❌ Not documented

**Need to Document**:
- Proxmox VE version (check: `pveversion`)
- ISO download source
- Installation method
- Initial network configuration
  - Interface: `enp3s0`
  - Bridge: `vmbr0` (10.25.1.5/24)
  - Gateway: 10.25.1.1
- Hostname: `pve-rover01`
- Storage configuration:
  - `local`: /var/lib/vz (images, snippets, vztmpl, backup, iso, rootdir)
  - `data`: LVM (vgname: pve) - rootdir, images
  - Disabled PBS: proxmoxbacksrv (10.16.1.41)

**Create Document**: `infrastructure/proxmox-installation.md`

### 1.2 Proxmox Post-Installation
**Status**: ❌ Not documented

**Need to Document**:
- Repository configuration (Enterprise vs No-Subscription)
- Update procedure
- Package installations
- Timezone/locale settings
- Root SSH key setup

**Create Document**: `infrastructure/proxmox-setup.md`

### 1.3 Storage Mount Configuration
**Status**: ❌ Not documented

**Critical Finding**: All media containers have mount point:
```
mp0: /mnt/pve/terra,mp=/media/Downloads
```

**Need to Document**:
- What is `/mnt/pve/terra`? (Appears to be shared storage)
- How is it mounted on Proxmox host?
- Is it NFS/CIFS/local disk?
- Mount configuration in `/etc/fstab`?
- Permissions and ownership

**Create Document**: `infrastructure/storage-configuration.md`

---

## 2. Container Infrastructure-as-Code

### 2.1 Container Creation Scripts
**Status**: ❌ Not documented

**Current State**:
- Most containers use community-scripts from ProxmoxVE helpers
- Each container has different specifications (CPU, RAM, disk)
- Special configurations for some containers (device passthrough, USB)

**Need to Create**:
- Automated container provisioning scripts
- Terraform or Ansible playbooks for container creation
- Or: Bash scripts using `pct create` commands

**Containers to Provision** (17 total):
1. **VM 100**: haosova-6.6 (QEMU VM - Home Assistant)
2. **LXC 101**: rover-plexd (Plex + hardware passthrough)
3. **LXC 103**: rova-glance (Dashboard)
4. **LXC 104**: rova-docka (Docker host)
5. **LXC 105**: rover-sabnzbd-old (SABnzbd old)
6. **LXC 106**: rova-pihole (DNS/Ad blocking)
7. **LXC 107**: rova-transmission (Torrent client)
8. **LXC 108**: rova-sabnzbd (SABnzbd)
9. **LXC 109**: rova-sonarr (TV management)
10. **LXC 110**: rova-radarr (Movie management)
11. **LXC 111**: rova-tailscale (VPN)
12. **LXC 112**: rova-filerr (File management)
13. **LXC 113**: rova-cloudflared (Cloudflare Tunnel)
14. **LXC 114**: rova-beszel (Monitoring agent hub)
15. **LXC 115**: rova-vscode-srv (VS Code server)
16. **LXC 116**: rova-checkmk (Monitoring)
17. **LXC 117**: ansible (Automation control node)

**Special Considerations**:
- Device passthrough (Plex needs GPU/USB)
- USB device mapping for multiple containers
- Mount points for shared media storage
- Unprivileged vs privileged containers

**Create Document**: `infrastructure/container-provisioning/`
- `README.md` - Overview and execution order
- `provision-all.sh` - Master script
- Individual container scripts or Terraform configs

### 2.2 Container Base Configuration
**Status**: ❌ Partially documented

**Need to Document for Each Container**:
- Base template used (Debian 12, Ubuntu, etc.)
- Initial package installations
- User/group creation
- Service installation method
- Systemd service configurations

**Create Document**: `infrastructure/container-configurations/`

---

## 3. Application Configurations

### 3.1 Service-Specific Configs
**Status**: ⚠️ Partially documented (Traefik only)

**Need to Document**:

#### Traefik (rova-docka)
- [x] Docker compose file (already captured)
- [x] config.yml (already captured)
- [ ] traefik.yml (need to backup)
- [ ] Environment variables
- [ ] Certificate storage (acme.json management)

#### Docker Containers (rova-docka)
- [x] Traefik
- [x] Portainer (installation method?)
- [x] Cloudflare DDNS
- [x] Beszel agent
- [ ] How Portainer was initially deployed
- [ ] Network creation (proxy network)

#### Arr Stack
- [ ] Sonarr configuration export
- [ ] Radarr configuration export
- [ ] Connection to SABnzbd
- [ ] Media folder structure
- [ ] Indexer configurations (without API keys)

#### Download Clients
- [ ] SABnzbd configuration
- [ ] Transmission configuration
- [ ] Download folder structure

#### Networking Services
- [ ] Pi-hole configuration
- [ ] Cloudflared tunnel configuration
- [ ] Tailscale setup and auth

#### Monitoring
- [ ] Beszel hub configuration
- [ ] CheckMK site configuration
- [ ] Agent deployments

#### Plex
- [ ] Installation method
- [ ] Library structure
- [ ] Hardware transcoding config

**Create Documents**: `applications/<service>/`
- `configuration.md`
- Config file templates

### 3.2 Application Data Exclusions
**Status**: ❌ Not documented

**Need to Define**:
- What data gets backed up vs rebuilt?
- Database exports needed?
- Configuration exports vs data?

Example decisions:
- Plex: Config yes, media library metadata export, actual media files excluded
- Sonarr/Radarr: Config exports, series/movie database
- Pi-hole: Blocklist configs, query history excluded
- CheckMK: Monitoring config, historical data excluded

**Create Document**: `infrastructure/data-management.md`

---

## 4. External Dependencies

### 4.1 Cloudflare Configuration
**Status**: ⚠️ Partially documented

**Need to Document**:
- Cloudflare account setup
- Domain DNS records (all current records)
- Cloudflare Tunnel creation and configuration
- API token creation and permissions
- DNS-01 challenge setup for Let's Encrypt

**Create Document**: `external-services/cloudflare.md`

### 4.2 OPNsense Firewall Configuration
**Status**: ⚠️ Partially documented (DNS overrides only)

**Need to Document**:
- Complete firewall rules
- NAT configuration
- DHCP server settings
- Unbound DNS full configuration
- Interface assignments
- VLANs (if any)
- Backup/restore procedure

**Create Document**: `external-services/opnsense-configuration.md`

### 4.3 External Storage/NAS
**Status**: ❌ Not documented

**Need to Document**:
- What is `/mnt/pve/terra`?
- Is there a NAS device?
- Storage server configuration
- Share configurations
- Mount instructions

**Create Document**: `external-services/nas-storage.md`

---

## 5. Secrets Management

### 5.1 Secrets Inventory
**Status**: ❌ Not documented

**Need to Document** (without actual secrets):
- List of all secrets/credentials needed
- Where each secret is used
- Secret generation instructions
- Recommended secret management tool

**Secrets Required**:
- Proxmox root password
- LXC container passwords
- Cloudflare API tokens
- Docker registry credentials (if any)
- Service API keys (Sonarr, Radarr indexers, etc.)
- Monitoring service credentials
- Let's Encrypt email
- Git SSH keys
- OPNsense admin password

**Create Document**: `infrastructure/secrets-management.md`

### 5.2 Ansible Vault Setup
**Status**: ❌ Not documented

**Need to Document**:
- Ansible vault creation
- Secret encryption
- Vault password management
- Variable structure

**Create Document**: `ansible/vault-setup.md`

---

## 6. Automation & Orchestration

### 6.1 Ansible Playbooks
**Status**: ⚠️ Partially documented

**Have**:
- [x] Inventory file
- [x] Update playbook

**Need**:
- [ ] Initial container configuration playbook
- [ ] SSH key distribution playbook
- [ ] Service installation playbooks
- [ ] Configuration deployment playbooks
- [ ] Health check playbooks

**Create Documents**: `ansible/playbooks/`

### 6.2 Rebuild Order & Dependencies
**Status**: ❌ Not documented

**Need to Document**:
```
1. Install Proxmox VE
2. Configure storage
3. Create containers in dependency order:
   - Ansible first (or manual SSH)
   - Pi-hole (DNS needed by others)
   - Docker host (Traefik needed for services)
   - Cloudflared (tunnel for external access)
   - Services (can be parallel)
4. Deploy applications
5. Configure Traefik routing
6. Configure OPNsense DNS overrides
7. Test services
```

**Create Document**: `REBUILD.md` (step-by-step rebuild guide)

---

## 7. Terraform Infrastructure-as-Code (Optional)

### 7.1 Terraform for Proxmox
**Status**: ❌ Not implemented

**Consider Implementing**:
- Terraform provider for Proxmox
- Define all containers as code
- State management
- Variable management for secrets

**Benefits**:
- Declarative infrastructure
- Version controlled
- Reproducible
- Easier to maintain

**Create Documents**: `terraform/`
- Provider configuration
- Container resources
- Network configuration
- Variables and outputs

---

## 8. Testing & Validation

### 8.1 Validation Scripts
**Status**: ❌ Not documented

**Need to Create**:
- Service health check scripts
- Connectivity validation
- DNS resolution tests
- SSL certificate validation
- End-to-end test suite

**Create Document**: `testing/validation.md`

### 8.2 Smoke Tests
**Status**: ❌ Not documented

**Need to Create**:
- Post-deployment smoke tests
- Service availability checks
- Integration tests

**Create Document**: `testing/smoke-tests.sh`

---

## 9. Backup & Restore Procedures

### 9.1 Backup Strategy
**Status**: ❌ Not documented

**Need to Document**:
- What gets backed up?
- Backup schedule
- Backup storage location
- Retention policy
- Proxmox Backup Server setup (currently disabled)

**Create Document**: `operations/backup-strategy.md`

### 9.2 Disaster Recovery
**Status**: ❌ Not documented

**Need to Document**:
- Recovery Time Objective (RTO)
- Recovery Point Objective (RPO)
- Step-by-step recovery procedures
- Testing procedures

**Create Document**: `operations/disaster-recovery.md`

---

## 10. Documentation Gaps

### Missing Documentation
- [ ] Service dependencies diagram
- [ ] Data flow diagrams
- [ ] Port mapping reference
- [ ] Firewall rules reference
- [ ] Update procedures for each service
- [ ] Troubleshooting runbooks
- [ ] Performance tuning notes
- [ ] Capacity planning

---

## Implementation Priority

### Phase 1: Critical Infrastructure (Week 1)
**Goal**: Be able to rebuild Proxmox and containers

1. Document Proxmox installation and configuration
2. Document storage configuration (/mnt/pve/terra)
3. Create container provisioning scripts/Terraform
4. Document secrets management approach
5. Create master rebuild guide

### Phase 2: Application Configuration (Week 2)
**Goal**: Be able to redeploy all applications

6. Export and document all service configurations
7. Create Ansible playbooks for app deployment
8. Document Docker container deployment
9. Document Traefik configuration deployment
10. Test rebuild in isolated environment

### Phase 3: External Services (Week 3)
**Goal**: Complete external dependencies

11. Document Cloudflare setup completely
12. Export OPNsense configuration
13. Document NAS/storage configuration
14. Create secrets vault structure

### Phase 4: Automation & Testing (Week 4)
**Goal**: Fully automated rebuild

15. Create end-to-end automation
16. Build validation test suite
17. Document backup/restore procedures
18. Create CI/CD for infrastructure updates
19. Test complete rebuild from scratch

---

## Recommended Tools

### Infrastructure-as-Code
- **Terraform**: Container provisioning
- **Ansible**: Configuration management
- **Proxmox Terraform Provider**: [Telmate/proxmox](https://github.com/Telmate/terraform-provider-proxmox)

### Secrets Management
- **Ansible Vault**: Built-in encrypted variables
- **SOPS**: More advanced secret management
- **1Password/Bitwarden CLI**: Secret injection

### Backup
- **Proxmox Backup Server**: Native backup solution
- **Restic**: Encrypted backups
- **Borg**: Deduplicated backups

### Testing
- **Molecule**: Ansible testing
- **Terratest**: Terraform testing
- **InSpec**: Infrastructure validation

---

## Success Criteria

You'll know you're done when:

1. ✅ Fresh Proxmox install + run single script = complete working environment
2. ✅ All secrets externalized and documented (but not committed)
3. ✅ Zero manual steps required
4. ✅ Complete rebuild takes < 2 hours
5. ✅ All services pass health checks
6. ✅ Documentation tested by someone else successfully

---

## Next Steps

1. **Start with storage discovery**: What is `/mnt/pve/terra`?
2. **Export container configs**: Save all `pct config` outputs
3. **Create container provisioning**: Start with simplest (glance, pihole)
4. **Build incrementally**: Add one container at a time to automation
5. **Test frequently**: Rebuild in test environment

---

## Questions to Answer

1. **Storage**: What is /mnt/pve/terra? NAS? Local disk? How is it mounted?
2. **Home Assistant VM**: VM 100 (QEMU) - different from LXC, needs special handling?
3. **Community Scripts**: Do these need network access during build? How to handle offline builds?
4. **Hardware Dependencies**: What hardware does Plex need passed through? GPU model?
5. **External Access**: Tailscale configuration - how are auth keys managed?
6. **Backup Server**: PBS at 10.16.1.41 is disabled - why? Should it be re-enabled?

---

## Repository Structure Proposal

```
homelab-docs/
├── README.md
├── REBUILD.md                      # ← NEW: Master rebuild guide
├── INVENTORY.md
├── NETWORK.md
├── SERVICES.md
├── ansible/
│   ├── README.md
│   ├── inventory/
│   ├── playbooks/                  # ← NEW: All playbooks
│   │   ├── provision-containers.yml
│   │   ├── configure-services.yml
│   │   ├── deploy-docker.yml
│   │   └── health-checks.yml
│   ├── roles/                      # ← NEW: Ansible roles
│   └── vault-setup.md              # ← NEW
├── infrastructure/                 # ← NEW: Core infrastructure
│   ├── proxmox-installation.md
│   ├── proxmox-setup.md
│   ├── storage-configuration.md
│   ├── secrets-management.md
│   ├── data-management.md
│   └── container-provisioning/
│       ├── README.md
│       ├── provision-all.sh
│       └── containers/             # Individual scripts
├── terraform/                      # ← NEW: IaC (optional)
│   ├── main.tf
│   ├── variables.tf
│   ├── proxmox.tf
│   └── containers/
├── applications/                   # ← NEW: App-specific config
│   ├── traefik/
│   ├── sonarr/
│   ├── radarr/
│   ├── plex/
│   └── [etc]/
├── external-services/              # ← NEW: External dependencies
│   ├── cloudflare.md
│   ├── opnsense-configuration.md
│   └── nas-storage.md
├── operations/                     # ← NEW: Operations docs
│   ├── backup-strategy.md
│   ├── disaster-recovery.md
│   └── maintenance.md
├── testing/                        # ← NEW: Tests
│   ├── validation.md
│   └── smoke-tests.sh
└── services/
    ├── README.md
    ├── adding-services.md
    └── docker.md
```

---

## Estimated Effort

- **Documentation**: 20-30 hours
- **Automation Development**: 30-40 hours
- **Testing**: 10-15 hours
- **Total**: 60-85 hours (~2 weeks full-time or 6-8 weeks part-time)

**ROI**: One catastrophic failure recovery = worth the investment!
