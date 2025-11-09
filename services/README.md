# Service Documentation

Documentation for individual services running in the homelab.

## Available Documentation

### [Adding New Services](adding-services.md)
**Complete step-by-step guide for adding new web-accessible services**

This comprehensive guide covers:
- Split-brain DNS architecture explanation
- Traefik configuration (routers and services)
- OPNsense DNS Host Override setup
- Cloudflare DNS configuration
- Testing and troubleshooting
- Complete example using Radarr

**Start here when adding any new service to the infrastructure.**

---

### [Docker Infrastructure](docker.md)
**Docker containers and management on rova-docka**

Covers:
- All running containers (Traefik, Portainer, Cloudflare DDNS, Beszel)
- Docker Compose configurations
- Volume and network details
- Management and update commands
- Integration with Cloudflare Tunnel

---

### [Traefik Configuration](traefik.md) *(Coming Soon)*
**Detailed Traefik reverse proxy documentation**

Will cover:
- Complete configuration breakdown
- Middleware usage
- Certificate management
- Dynamic routing
- Custom configurations

---

## Quick Links

- [Main Documentation](../README.md)
- [Services Catalog](../SERVICES.md) - All service URLs
- [Network Documentation](../NETWORK.md) - Architecture details
- [Inventory](../INVENTORY.md) - All hosts and IPs

## Related Topics

### DNS Configuration
For DNS setup details, see:
- [Adding New Services](adding-services.md#step-3-add-internal-dns-override-opnsense) - OPNsense DNS configuration
- [Network Documentation](../NETWORK.md) - DNS architecture overview

### Reverse Proxy
For reverse proxy details, see:
- [Adding New Services](adding-services.md#step-2-add-traefik-configuration) - Traefik router setup
- [Docker Infrastructure](docker.md) - Traefik container details
