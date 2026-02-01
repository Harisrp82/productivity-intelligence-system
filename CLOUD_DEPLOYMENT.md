# Cloud Deployment Guide - Oracle Cloud Free Tier

Deploy your Productivity Intelligence System to Oracle Cloud for **free, 24/7 operation**.

---

## Table of Contents
1. [Create Oracle Cloud Account](#1-create-oracle-cloud-account)
2. [Create Free VM Instance](#2-create-free-vm-instance)
3. [Connect to Your VM](#3-connect-to-your-vm)
4. [Set Up the Environment](#4-set-up-the-environment)
5. [Transfer Project Files](#5-transfer-project-files)
6. [Configure Google OAuth](#6-configure-google-oauth)
7. [Set Up Cron Jobs](#7-set-up-cron-jobs)
8. [Verify Deployment](#8-verify-deployment)
9. [Monitoring & Maintenance](#9-monitoring--maintenance)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Create Oracle Cloud Account

### Step 1.1: Sign Up
1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. Click **"Start for free"**
3. Fill in your details:
   - Email address
   - Country: India (or your country)
   - Name and address

### Step 1.2: Verify Identity
- You'll need a credit/debit card for verification
- **You will NOT be charged** - this is just for identity verification
- Oracle's Always Free tier is genuinely free forever

### Step 1.3: Select Home Region
- Choose **"India South (Hyderabad)"** or **"India West (Mumbai)"** for lowest latency
- This cannot be changed later, so choose wisely

### Step 1.4: Complete Setup
- Wait for account provisioning (usually 5-10 minutes)
- You'll receive a confirmation email

---

## 2. Create Free VM Instance

### Step 2.1: Access Compute
1. Log into [Oracle Cloud Console](https://cloud.oracle.com/)
2. Click the hamburger menu (☰) → **Compute** → **Instances**
3. Click **"Create Instance"**

### Step 2.2: Configure Instance
```
Name: productivity-intelligence
Compartment: (root) [default]
```

### Step 2.3: Select Image and Shape (IMPORTANT)
1. Click **"Edit"** in the "Image and shape" section
2. **Image**: Oracle Linux 8 (or Ubuntu 22.04)
3. **Shape**: Click "Change Shape"
   - Select **"Ampere"** (ARM-based) for Always Free
   - Or **"AMD"** → **"VM.Standard.E2.1.Micro"** (Always Free)
   - **IMPORTANT**: Look for shapes marked "Always Free Eligible"

Recommended Always Free shapes:
| Shape | CPU | RAM | Always Free |
|-------|-----|-----|-------------|
| VM.Standard.E2.1.Micro | 1 OCPU | 1 GB | Yes |
| VM.Standard.A1.Flex | 1-4 OCPU | 6-24 GB | Yes (up to 4 OCPU, 24GB total) |

Choose **VM.Standard.A1.Flex** with 1 OCPU and 6 GB RAM for best free option.

### Step 2.4: Configure Networking
- **Virtual Cloud Network**: Create new VCN (or use existing)
- **Subnet**: Create new public subnet
- **Public IPv4 address**: Select **"Assign a public IPv4 address"** ✓

### Step 2.5: Add SSH Keys
1. Select **"Generate a key pair for me"**
2. Click **"Save Private Key"** - download and save securely as `oracle-vm-key.key`
3. Also save the public key

**IMPORTANT**: Keep this private key safe! You need it to connect to your VM.

### Step 2.6: Create Instance
1. Click **"Create"**
2. Wait for instance state to show **"Running"** (2-5 minutes)
3. Note the **Public IP Address** displayed

---

## 3. Connect to Your VM

### Step 3.1: Windows - Using PowerShell/SSH

```powershell
# Set correct permissions on key file (run once)
icacls oracle-vm-key.key /inheritance:r /grant:r "%USERNAME%:R"

# Connect to VM
ssh -i oracle-vm-key.key opc@<YOUR_PUBLIC_IP>
```

Replace `<YOUR_PUBLIC_IP>` with your instance's public IP.

### Step 3.2: Windows - Using PuTTY (Alternative)

1. Download [PuTTY](https://www.putty.org/)
2. Convert key using PuTTYgen:
   - Load `oracle-vm-key.key`
   - Save as `.ppk` file
3. In PuTTY:
   - Host: `<YOUR_PUBLIC_IP>`
   - Connection → SSH → Auth → Browse for `.ppk` file
   - Connection → Data → Auto-login username: `opc`
   - Click "Open"

### Step 3.3: Verify Connection
Once connected, you should see:
```
[opc@productivity-intelligence ~]$
```

---

## 4. Set Up the Environment

Run these commands on your Oracle VM:

### Step 4.1: Update System
```bash
# For Oracle Linux
sudo dnf update -y

# Install required packages
sudo dnf install -y python39 python39-pip git
```

### Step 4.2: Set Up Python
```bash
# Check Python version
python3.9 --version

# Create alias for convenience
echo 'alias python=python3.9' >> ~/.bashrc
echo 'alias pip=pip3.9' >> ~/.bashrc
source ~/.bashrc
```

### Step 4.3: Create Project Directory
```bash
# Create directory
mkdir -p ~/productivity-intelligence
cd ~/productivity-intelligence

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate
```

### Step 4.4: Set Timezone (Important!)
```bash
# Set to Indian Standard Time
sudo timedatectl set-timezone Asia/Kolkata

# Verify
timedatectl
```

---

## 5. Transfer Project Files

### Option A: Clone from GitHub (Recommended)

On your Oracle VM:
```bash
cd ~
git clone https://github.com/Harisrp82/productivity-intelligence-system.git productivity-intelligence
cd productivity-intelligence
```

### Option B: Upload via SCP (From Windows)

On your Windows machine:
```powershell
# Upload entire project folder
scp -i oracle-vm-key.key -r "D:\Projects\Amazfit Watch Project\*" opc@<YOUR_PUBLIC_IP>:~/productivity-intelligence/
```

### Step 5.1: Install Dependencies
On the Oracle VM:
```bash
cd ~/productivity-intelligence
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5.2: Create .env File
```bash
nano .env
```

Add your configuration:
```env
GROK_API_KEY=your_grok_api_key_here
GOOGLE_DOC_ID=your_google_doc_id_here
DATABASE_URL=sqlite:///productivity.db
TIMEZONE=Asia/Kolkata
```

Press `Ctrl+O` to save, `Ctrl+X` to exit.

---

## 6. Configure Google OAuth

This is the trickiest part because Google OAuth normally requires a browser.

### Step 6.1: Prepare Credentials Locally (On Windows)

First, ensure your local setup works and you have valid tokens:
```powershell
cd "D:\Projects\Amazfit Watch Project"
python daily_workflow.py
```

This creates/refreshes `token.json` and `token_fit.json`.

### Step 6.2: Upload Credentials and Tokens

From Windows PowerShell:
```powershell
# Upload credentials.json
scp -i oracle-vm-key.key "D:\Projects\Amazfit Watch Project\credentials.json" opc@<YOUR_PUBLIC_IP>:~/productivity-intelligence/

# Upload token files
scp -i oracle-vm-key.key "D:\Projects\Amazfit Watch Project\token.json" opc@<YOUR_PUBLIC_IP>:~/productivity-intelligence/

scp -i oracle-vm-key.key "D:\Projects\Amazfit Watch Project\token_fit.json" opc@<YOUR_PUBLIC_IP>:~/productivity-intelligence/
```

### Step 6.3: Verify on VM
```bash
cd ~/productivity-intelligence
ls -la *.json
```

You should see:
```
credentials.json
token.json
token_fit.json
```

### Step 6.4: Test the Workflow
```bash
cd ~/productivity-intelligence
source venv/bin/activate
python daily_workflow.py
```

If successful, you'll see the workflow run and report sent to Google Docs.

### Step 6.5: Token Refresh Note

Google OAuth tokens expire after some time. The tokens should auto-refresh, but if you get authentication errors:

1. Run the workflow locally on Windows to refresh tokens
2. Re-upload the token files to the VM

---

## 7. Set Up Cron Jobs

Cron is the Linux equivalent of Windows Task Scheduler.

### Step 7.1: Create Runner Script
```bash
nano ~/productivity-intelligence/run_cloud.sh
```

Add:
```bash
#!/bin/bash
# Cloud runner script for Productivity Intelligence

cd /home/opc/productivity-intelligence
source venv/bin/activate

# Log file with date
LOG_FILE="/home/opc/productivity-intelligence/logs/wake_detector_$(date +%Y%m%d).log"

# Run wake detector
python wake_detector.py >> "$LOG_FILE" 2>&1
```

Save and make executable:
```bash
chmod +x ~/productivity-intelligence/run_cloud.sh
```

### Step 7.2: Create Logs Directory
```bash
mkdir -p ~/productivity-intelligence/logs
```

### Step 7.3: Set Up Cron Job
```bash
crontab -e
```

If prompted, choose `nano` as editor.

Add these lines (runs every 30 mins from 8 AM to 2 PM IST):
```cron
# Productivity Intelligence - Wake Detector
# Runs every 30 minutes from 8:00 AM to 2:00 PM IST

0 8 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 8 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 9 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 9 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 10 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 10 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 11 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 11 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 12 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 12 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 13 * * * /home/opc/productivity-intelligence/run_cloud.sh
30 13 * * * /home/opc/productivity-intelligence/run_cloud.sh
0 14 * * * /home/opc/productivity-intelligence/run_cloud.sh
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

### Step 7.4: Verify Cron
```bash
crontab -l
```

---

## 8. Verify Deployment

### Step 8.1: Manual Test
```bash
cd ~/productivity-intelligence
source venv/bin/activate
python wake_detector.py
```

Expected output:
```
============================================================
Wake Detector - Checking for wake...
============================================================
Wake detected! Time: 13:49, Sleep: 7.8h
...
SUCCESS! Daily report generated and sent to Google Docs
============================================================
```

### Step 8.2: Check Logs
```bash
# View today's log
cat ~/productivity-intelligence/logs/wake_detector_$(date +%Y%m%d).log

# Or tail for live updates
tail -f ~/productivity-intelligence/logs/wake_detector_*.log
```

### Step 8.3: Check Cron is Running
```bash
# View cron logs
sudo grep CRON /var/log/cron

# Or check system journal
sudo journalctl -u crond --since "today"
```

---

## 9. Monitoring & Maintenance

### Daily Log Check
```bash
# SSH into VM
ssh -i oracle-vm-key.key opc@<YOUR_PUBLIC_IP>

# Check today's log
cat ~/productivity-intelligence/logs/wake_detector_$(date +%Y%m%d).log
```

### Keep VM Running
Oracle Cloud VMs stay running unless you stop them. To ensure uptime:
1. Don't manually stop the instance
2. Oracle may reclaim "idle" resources - running cron jobs prevents this

### Update Code from GitHub
```bash
cd ~/productivity-intelligence
git pull origin main
```

### Refresh Google Tokens (If Needed)
If you get authentication errors:
1. Run workflow locally on Windows
2. Re-upload tokens:
```powershell
scp -i oracle-vm-key.key "D:\Projects\Amazfit Watch Project\token*.json" opc@<YOUR_PUBLIC_IP>:~/productivity-intelligence/
```

### Log Rotation (Optional)
Add to crontab to clean old logs weekly:
```cron
# Clean logs older than 7 days (runs every Sunday at midnight)
0 0 * * 0 find /home/opc/productivity-intelligence/logs -name "*.log" -mtime +7 -delete
```

---

## 10. Troubleshooting

### "Permission denied" when connecting via SSH
```bash
# On Windows, fix key permissions
icacls oracle-vm-key.key /inheritance:r /grant:r "%USERNAME%:R"
```

### "Connection refused" or can't connect
1. Check instance is running in Oracle Cloud Console
2. Verify Security List allows SSH (port 22):
   - Go to: Networking → Virtual Cloud Networks → Your VCN → Security Lists
   - Ensure ingress rule exists for port 22

### "Module not found" errors
```bash
cd ~/productivity-intelligence
source venv/bin/activate
pip install -r requirements.txt
```

### "Invalid credentials" or Google Auth fails
1. Re-run workflow locally on Windows to refresh tokens
2. Re-upload `token.json` and `token_fit.json` to VM

### Cron jobs not running
```bash
# Check cron service status
sudo systemctl status crond

# If not running, start it
sudo systemctl start crond
sudo systemctl enable crond

# Check cron logs for errors
sudo grep CRON /var/log/cron
```

### Check if wake detector state is stuck
```bash
# View state file
cat ~/productivity-intelligence/.wake_detector_state.json

# Reset if needed (forces re-run tomorrow)
rm ~/productivity-intelligence/.wake_detector_state.json
```

### VM running out of disk space
```bash
# Check disk usage
df -h

# Clean old logs
find ~/productivity-intelligence/logs -name "*.log" -mtime +30 -delete

# Clean pip cache
pip cache purge
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Connect to VM | `ssh -i oracle-vm-key.key opc@<IP>` |
| Check logs | `cat ~/productivity-intelligence/logs/wake_detector_$(date +%Y%m%d).log` |
| Manual run | `cd ~/productivity-intelligence && source venv/bin/activate && python wake_detector.py` |
| View cron jobs | `crontab -l` |
| Edit cron jobs | `crontab -e` |
| Check cron status | `sudo systemctl status crond` |
| Update from GitHub | `cd ~/productivity-intelligence && git pull` |
| Check disk space | `df -h` |

---

## Cost Summary

| Resource | Cost |
|----------|------|
| Oracle Cloud VM (Always Free) | $0 |
| Storage (up to 200GB free) | $0 |
| Network (10TB egress free) | $0 |
| **Total Monthly Cost** | **$0** |

---

## Next Steps After Deployment

1. **Disable Windows Task Scheduler** (since cloud handles it now)
   - Open Task Scheduler
   - Find "ProductivityIntelligence-WakeDetector"
   - Right-click → Disable

2. **Monitor for a few days** to ensure everything works

3. **Set up email alerts** (optional) for failures - see Oracle Cloud Monitoring

---

---

## 11. Deploy Live Dashboard (Optional)

Run your real-time dashboard on Oracle Cloud so you can access it from anywhere.

### Step 11.1: Install Gunicorn (Production Server)

On Oracle VM:
```bash
cd ~/productivity-intelligence
source venv/bin/activate
pip install gunicorn
```

### Step 11.2: Open Port 5000 in Oracle Cloud

1. Go to Oracle Cloud Console → **Networking** → **Virtual Cloud Networks**
2. Click on your VCN → **Security Lists** → **Default Security List**
3. Click **"Add Ingress Rules"**
4. Add rule:
   - **Source CIDR**: `0.0.0.0/0`
   - **Destination Port Range**: `5000`
   - **Description**: `Dashboard HTTP`
5. Click **"Add Ingress Rules"**

### Step 11.3: Open Firewall on VM

Run on Oracle VM:
```bash
# For Oracle Linux
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

### Step 11.4: Test Dashboard Manually

```bash
cd ~/productivity-intelligence
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 dashboard_server:app
```

Open in browser: `http://<YOUR_PUBLIC_IP>:5000`

Press `Ctrl+C` to stop after testing.

### Step 11.5: Set Up as System Service

Create systemd service:
```bash
sudo nano /etc/systemd/system/dashboard.service
```

Paste:
```ini
[Unit]
Description=Productivity Intelligence Dashboard Server
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/productivity-intelligence
Environment="PATH=/home/opc/productivity-intelligence/venv/bin"
ExecStart=/home/opc/productivity-intelligence/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 dashboard_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

### Step 11.6: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable dashboard

# Start the service
sudo systemctl start dashboard

# Check status
sudo systemctl status dashboard
```

### Step 11.7: Verify Dashboard

Open in browser: `http://<YOUR_PUBLIC_IP>:5000`

You should see your live dashboard with real-time data!

### Dashboard Service Commands

| Task | Command |
|------|---------|
| Start dashboard | `sudo systemctl start dashboard` |
| Stop dashboard | `sudo systemctl stop dashboard` |
| Restart dashboard | `sudo systemctl restart dashboard` |
| Check status | `sudo systemctl status dashboard` |
| View logs | `sudo journalctl -u dashboard -f` |

### Optional: Custom Domain with HTTPS

For a custom domain with HTTPS:
1. Register a domain (or use free subdomain from services like DuckDNS)
2. Point domain to your Oracle VM's public IP
3. Install Nginx as reverse proxy
4. Use Certbot for free SSL certificate

```bash
# Install Nginx
sudo dnf install nginx -y

# Configure Nginx (example)
sudo nano /etc/nginx/conf.d/dashboard.conf
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Get SSL certificate (after domain is pointing to IP)
sudo dnf install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

Congratulations! Your Productivity Intelligence System is now running 24/7 in the cloud for free.
