# Communications Server Deployment Guide

Production deployment instructions for the Faculty Course Assignment Solver Server.

## Prerequisites

- Linux server with root/sudo access
- Python 3.8+
- nginx installed
- Git installed

## Deployment Steps

### 1. Clone Repository on Server
```bash
sudo mkdir -p /opt/faculty_course_assignment
sudo chown $USER:$USER /opt/faculty_course_assignment
cd /opt/faculty_course_assignment
git clone https://github.com/dsu-cs/faculty_course_assignment.git .
git checkout main
```

### 2. Setup Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create Log Directories
```bash
sudo mkdir -p /var/log/solver
sudo mkdir -p /var/run/solver
sudo chown www-data:www-data /var/log/solver
sudo chown www-data:www-data /var/run/solver
```

### 4. Install nginx Configuration
```bash
sudo cp solver_server/communications/deployment/nginx.conf /etc/nginx/sites-available/solver
sudo ln -s /etc/nginx/sites-available/solver /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Install systemd Service
```bash
sudo cp solver_server/communications/deployment/solver-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable solver-server
sudo systemctl start solver-server
```

### 6. Verify Deployment
```bash
# Check service status
sudo systemctl status solver-server

# Check logs
sudo journalctl -u solver-server -f

# Test endpoint
curl http://localhost/health
```

## Server Management

### Start Service
```bash
sudo systemctl start solver-server
```

### Stop Service
```bash
sudo systemctl stop solver-server
```

### Restart Service
```bash
sudo systemctl restart solver-server
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u solver-server -f

# Access logs
sudo tail -f /var/log/solver/access.log

# Error logs
sudo tail -f /var/log/solver/error.log
```

## Troubleshooting

### Service Won't Start
Check logs: `sudo journalctl -u solver-server -xe`

### Permission Errors
Ensure www-data owns log directories:
```bash
sudo chown -R www-data:www-data /var/log/solver
sudo chown -R www-data:www-data /var/run/solver
```

### nginx Errors
Test config: `sudo nginx -t`
Reload: `sudo systemctl reload nginx`

## Notes for Tyler

This configuration is ready for deployment to the DSU Linux server.

Requires coordination with Eric Home for:
- Server access
- DNS configuration for solver.dsu.edu
- Firewall rules for port 80

Let me know if you need any adjustments to the configuration.
