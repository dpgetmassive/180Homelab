# Docker Infrastructure (rova-docka)

Host: `rova-docka` (10.25.1.12)

## Overview

The rova-docka LXC container serves as the primary Docker host for the homelab infrastructure. It runs critical services including the Traefik reverse proxy, Portainer container management UI, Cloudflare DDNS updater, and Beszel monitoring agent.

## Running Containers

### 1. Traefik (Reverse Proxy)
- **Image**: `traefik:latest`
- **Container Name**: `traefik`
- **Ports**: 80:80 (HTTP), 443:443 (HTTPS)
- **Network**: `proxy` (bridge)
- **Compose File**: `/dockerland/traefik/docker-compose.yaml`
- **Purpose**: 
  - Reverse proxy for all web services
  - Automatic HTTPS with Let's Encrypt wildcard certificates
  - Routes traffic for *.rova.getmassive.com.au domain
  - Integrates with Cloudflare DNS-01 challenge for certificate validation

**Key Configuration**:
- Uses Cloudflare API for DNS challenge (email: dp@getmassive.com.au)
- Dashboard accessible at: `traefik-dashboard.rova.getmassive.com.au`
- Basic auth protected with user: `dp`
- Wildcard certificate for `*.rova.getmassive.com.au`

**Volumes**:
- `/dockerland/traefik/traefik.yml` → `/traefik.yml` (main config)
- `/dockerland/traefik/config.yml` → `/config.yml` (dynamic routing)
- `/dockerland/traefik/acme.json` → `/acme.json` (SSL certificates)
- `/var/run/docker.sock` → Docker socket for service discovery

### 2. Portainer (Container Management)
- **Image**: `portainer/portainer-ce:latest`
- **Container Name**: `portainer`
- **Ports**: 8000:8000, 9443:9443 (HTTPS UI)
- **Purpose**: Web UI for managing Docker containers across the homelab
- **Access**: `portainer.rova.getmassive.com.au` (via Traefik)

**Volumes**:
- `portainer_data` volume → `/data` (persistent config)
- `/var/run/docker.sock` → Docker socket for management

### 3. Cloudflare DDNS
- **Image**: `timothyjmiller/cloudflare-ddns:latest`
- **Container Name**: `cloudflare-ddns`
- **Network Mode**: `host`
- **Compose File**: `/dockerland/cloudflare-ddns/docker-compose.yml`
- **Purpose**: Automatically updates DNS records when public IP changes
- **Config**: `/dockerland/cloudflare-ddns/config.json`

**Configuration**:
- Updates: `rova.getmassive.com.au` subdomain
- Update interval: 300 seconds (5 minutes)
- Proxied through Cloudflare (orange cloud enabled)

### 4. Beszel Agent (Monitoring)
- **Image**: `henrygd/beszel-agent`
- **Container Name**: `beszel-agent`
- **Purpose**: System monitoring agent reporting to rova-beszel (10.25.1.20)
- **Volumes**: `/var/run/docker.sock` → Docker metrics collection

## Docker Networks

- **proxy** (bridge): Used by Traefik and services requiring reverse proxy
- **glance_default** (bridge): Used by Glance dashboard service
- **host**: Used by cloudflare-ddns for direct network access
- **bridge**: Default Docker bridge network

## Docker Volumes

- **portainer_data**: Persistent storage for Portainer configuration and data

## Management Commands

### View Running Containers
```bash
ssh 10.25.1.12
docker ps
```

### View Container Logs
```bash
docker logs traefik
docker logs portainer
docker logs cloudflare-ddns
docker logs beszel-agent
```

### Restart Services
```bash
cd /dockerland/traefik
docker-compose restart

cd /dockerland/cloudflare-ddns
docker-compose restart
```

### Update Containers
```bash
# Update Traefik
cd /dockerland/traefik
docker-compose pull
docker-compose up -d

# Update Cloudflare DDNS
cd /dockerland/cloudflare-ddns
docker-compose pull
docker-compose up -d

# Update Portainer
docker pull portainer/portainer-ce:latest
docker stop portainer
docker rm portainer
# Re-run original docker run command

# Update Beszel Agent
docker pull henrygd/beszel-agent
docker stop beszel-agent
docker rm beszel-agent
# Re-run original docker run command
```

### Access Portainer UI
Open browser to: `https://portainer.rova.getmassive.com.au`

### Access Traefik Dashboard
Open browser to: `https://traefik-dashboard.rova.getmassive.com.au`
- Username: `dp`
- Password: (configured in basic auth)

## File Locations

```
/dockerland/
├── traefik/
│   ├── docker-compose.yaml
│   ├── traefik.yml          # Main Traefik configuration
│   ├── config.yml           # Dynamic routing rules
│   └── acme.json           # SSL certificates (chmod 600)
├── cloudflare-ddns/
│   ├── docker-compose.yml
│   └── config.json         # DDNS configuration
└── glance/
    └── docker-compose.yml   # Dashboard service (not currently running)
```

## Integration with Cloudflare Tunnel

The Docker infrastructure works in conjunction with the Cloudflare Tunnel:

1. External traffic arrives at Cloudflare edge
2. Cloudflare Tunnel (10.25.1.19) forwards to Traefik (10.25.1.12:443)
3. Traefik routes to appropriate backend services based on hostname
4. Traefik handles SSL termination with Let's Encrypt wildcard cert
5. Backend services receive proxied requests from Traefik

## Security Notes

- Traefik runs with `no-new-privileges:true` security option
- Cloudflare DDNS runs with `no-new-privileges:true` security option
- Traefik dashboard is protected with HTTP basic authentication
- All external services use HTTPS only (HTTP redirects to HTTPS)
- SSL certificates automatically renewed via Let's Encrypt
- Cloudflare API tokens stored in docker-compose files (consider using secrets)

## Monitoring

- Container status monitored by Beszel agent
- Metrics sent to rova-beszel (10.25.1.20)
- Traefik dashboard provides real-time routing information
- Portainer provides container health status

## Related Documentation

- See [NETWORK.md](../NETWORK.md) for Cloudflare Tunnel architecture
- See [traefik.md](traefik.md) for detailed Traefik configuration (coming soon)
- See [SERVICES.md](../SERVICES.md) for all web-accessible services
