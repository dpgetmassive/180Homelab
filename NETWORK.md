# Network Documentation

**Last Updated:** 2025-11-09

## Architecture: Cloudflare Tunnel (No Port Forwarding!)

External access uses **Cloudflare Tunnel** - completely secure, no ports open on firewall.

### Traffic Flow
```
Internet → Cloudflare → Tunnel → cloudflared (10.25.1.19) → Traefik (10.25.1.12) → Services
```

### Components

**Cloudflare Tunnel** (10.25.1.19 - rova-cloudflared)
- Secure outbound tunnel to Cloudflare
- No inbound ports required
- DDoS protection included

**Cloudflare DDNS** (10.25.1.12 - container)
- Updates DNS: rova.getmassive.com.au → 159.196.118.71
- Frequency: Every 300 seconds

**Traefik** (10.25.1.12 - rova-docka)
- SSL termination (Let's Encrypt wildcard cert)
- Routes traffic based on hostname

## Network Segments

- **Management:** 10.16.1.0/24 (Firewall at 10.16.1.1)
- **Homelab:** 10.25.1.0/24 (All services)

## Published Services

Via *.rova.getmassive.com.au through Cloudflare Tunnel:
- proxmox1.rova, portainer.rova, plex.rova, sonar.rova, sabnzb.rova, cmk-mon.rova

## Security Benefits

✅ No open ports on firewall  
✅ No NAT required  
✅ Outbound-only connections  
✅ Cloudflare DDoS protection  
✅ End-to-end SSL/TLS  

See [INVENTORY.md](INVENTORY.md) and [SERVICES.md](SERVICES.md) for details.
