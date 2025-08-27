# 🔍 Plex Mount Health Monitor

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg)](https://www.linux.org/)

> A robust monitoring solution for Plex media server storage mounts with automated email alerts

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Health Checks](#-health-checks)
- [Email Setup](#-email-setup)
- [Running as Service](#-running-as-service)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)

## ✨ Features

- 🔄 **Continuous Mount Monitoring** - Real-time health checks of storage mounts
- 📧 **Email Alerts** - Configurable notifications when issues are detected
- 🔒 **Secure Password Storage** - External password files for enhanced security
- 📊 **Comprehensive Logging** - Rotating logs with configurable levels
- 🧪 **Test Functionality** - SMTP connection testing and email verification
- ⚙️ **Flexible Configuration** - All settings controlled via configuration file
- 🚀 **Systemd Integration** - Run as a background service
- 🔍 **Multiple Health Checks** - Mount existence, accessibility, read/write tests
- 📁 **Critical Directory Monitoring** - Ensures important directories exist
- 🛡️ **Failure Threshold Management** - Prevents alert spam with consecutive failure tracking

## 🚀 Quick Start

1. **Clone and install:**
   ```bash
   git clone <repository-url>
   cd plex-mount-health-check
   sudo bash setup.sh
   ```

2. **Configure email settings:**
   ```bash
   sudo nano /opt/plex-mount-health/plex_mount_health.conf
   ```

3. **Test your setup:**
   ```bash
   cd /opt/plex-mount-health
   python3 plex_mount_health.py --test-smtp
   python3 plex_mount_health.py --test-email
   ```

4. **Start monitoring:**
   ```bash
   sudo systemctl enable plex-mount-health.service
   sudo systemctl start plex-mount-health.service
   ```

## 📦 Installation

### Requirements

- Python 3.6 or higher
- Linux system with `/proc/mounts` support
- SMTP server access for email notifications

### Automatic Installation

```bash
sudo bash setup.sh
```

The setup script will:
- ✅ Install files to `/opt/plex-mount-health/`
- ✅ Create systemd service
- ✅ Set proper permissions
- ✅ Test script syntax
- ✅ Optionally create secure password file

### Manual Installation

```bash
# Create installation directory
sudo mkdir -p /opt/plex-mount-health

# Copy files
sudo cp plex_mount_health.py /opt/plex-mount-health/
sudo cp plex_mount_health.conf /opt/plex-mount-health/
sudo chmod +x /opt/plex-mount-health/plex_mount_health.py
sudo chmod 600 /opt/plex-mount-health/plex_mount_health.conf
```

## ⚙️ Configuration

### Quick Configuration

Edit the main configuration file:

```bash
sudo nano /opt/plex-mount-health/plex_mount_health.conf
```

**Essential Settings:**

```ini
[Mount Settings]
mount_path = /mnt/your-storage-path

[Email Settings]
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_use_tls = true
smtp_username = your_email@gmail.com
smtp_password_file = /opt/plex-mount-health/.email_password
from_email = your_email@gmail.com
to_emails = admin@yourdomain.com
```

### Configuration Sections

| Section | Description |
|---------|-------------|
| **Mount Settings** | Mount path, check intervals, test file settings |
| **Logging** | Log file location, levels, rotation settings |
| **Script Behavior** | Debug mode, dry-run, failure thresholds |
| **Email Settings** | SMTP configuration and notification settings |
| **Email Test Settings** | Test email automation and customization |
| **Advanced Settings** | Critical directories, mount options |

## 💻 Usage

### Command Line Options

```bash
# Run single check and exit
python3 plex_mount_health.py --once

# Test SMTP connection (recommended first step)
python3 plex_mount_health.py --test-smtp

# Send test email
python3 plex_mount_health.py --test-email

# Run continuous monitoring (default)
python3 plex_mount_health.py

# Use custom configuration file
python3 plex_mount_health.py -c /path/to/custom.conf

# Show help
python3 plex_mount_health.py --help
```

### Example Output

```
INFO - Starting mount health check for: /mnt/storage
INFO - Mount Existence: PASS - Mount point exists and is mounted
INFO - Mount Accessibility: PASS - Mount is accessible for read/write operations
INFO - Read/Write Test: PASS - Read/write test successful
INFO - Critical Directories: PASS - All critical directories exist
INFO - Mount health check PASSED
```

## 🔍 Health Checks

The monitor performs these checks on each cycle:

| Check | Description | Failure Actions |
|-------|-------------|-----------------|
| **🔗 Mount Existence** | Verifies mount point exists and is mounted | Immediate alert |
| **🔓 Mount Accessibility** | Tests read and write permissions | Immediate alert |
| **📝 Read/Write Test** | Creates, writes, reads, and deletes test file | Immediate alert |
| **📁 Critical Directories** | Verifies important directories exist | Configurable alert |

## 📧 Email Setup

### Recommended: External SMTP Provider

#### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password: [Google Account → Security → App passwords](https://myaccount.google.com/apppasswords)
3. Configure:

```ini
[Email Settings]
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_use_tls = true
smtp_username = your_email@gmail.com
smtp_password_file = /opt/plex-mount-health/.email_password
```

#### Other Providers

| Provider | SMTP Server | Port | TLS |
|----------|-------------|------|-----|
| **Outlook** | `smtp-mail.outlook.com` | 587 | Yes |
| **Yahoo** | `smtp.mail.yahoo.com` | 587 | Yes |
| **Custom/ISP** | `mail.yourisp.com` | 25/587 | Varies |

### Secure Password Setup

```bash
# Create secure password file
echo "your_email_password" | sudo tee /opt/plex-mount-health/.email_password

# Secure the file
sudo chmod 600 /opt/plex-mount-health/.email_password
sudo chown root:root /opt/plex-mount-health/.email_password
```

### Test Email Features

- 🧪 **Manual Test**: `--test-email` parameter
- 🚀 **Startup Test**: `send_test_email_on_startup = true`
- ⏰ **Periodic Tests**: `test_email_interval_hours = 24`
- ✏️ **Custom Messages**: Configurable subject and body

## 🔄 Running as Service

### Systemd Service (Recommended)

```bash
# Enable automatic startup
sudo systemctl enable plex-mount-health.service

# Start the service
sudo systemctl start plex-mount-health.service

# Check status
sudo systemctl status plex-mount-health.service

# View logs
sudo journalctl -u plex-mount-health.service -f
```

### Cron Alternative

For periodic checks instead of continuous monitoring:

```bash
# Edit crontab
crontab -e

# Add entry to run every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/plex-mount-health/plex_mount_health.py --once
```

## 🛠️ Troubleshooting

### Common Issues

<details>
<summary>🔧 Email Authentication Errors</summary>

**Symptoms:** Authentication failures, login errors

**Solutions:**
- Use app passwords for Gmail/Outlook
- Verify SMTP server settings
- Check firewall rules for SMTP ports
- Test with `--test-smtp` command

</details>

<details>
<summary>🔧 Mount Detection Issues</summary>

**Symptoms:** Mount not detected, false negatives

**Solutions:**
- Verify mount path is correct
- Check if mount is actually mounted: `mount | grep your-path`
- Ensure `/proc/mounts` is accessible
- Test with `--once` command in debug mode

</details>

<details>
<summary>🔧 Permission Errors</summary>

**Symptoms:** Cannot create test files, access denied

**Solutions:**
- Run script with appropriate permissions
- Check mount point ownership and permissions
- Verify mount is not read-only
- Check filesystem space availability

</details>

### Debug Mode

Enable detailed troubleshooting:

```ini
[Script Behavior]
debug = true
```

This provides:
- ✅ Configuration values loaded
- ✅ Each health check step details
- ✅ Detailed error messages
- ✅ SMTP connection diagnostics

### Dry Run Mode

Test without making changes:

```ini
[Script Behavior]
dry_run = true
```

## 🔒 Security

### Best Practices

- 🔐 **Use password files** instead of storing passwords in config
- 🔒 **Secure file permissions**: `chmod 600` for sensitive files
- 🔑 **Use app passwords** for email providers
- 📋 **Regular password rotation**
- 📊 **Monitor log files** for security events

### File Permissions

```bash
# Configuration file
sudo chmod 600 /opt/plex-mount-health/plex_mount_health.conf

# Password file
sudo chmod 600 /opt/plex-mount-health/.email_password
sudo chown root:root /opt/plex-mount-health/.email_password

# Script executable
sudo chmod +x /opt/plex-mount-health/plex_mount_health.py
```

## 📊 Example Configurations

See [`email_config_examples.conf`](email_config_examples.conf) for complete working examples of:

- Gmail setup with app passwords
- Outlook/Hotmail configuration  
- Custom SMTP server setup
- Secure password file usage

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🆘 Support

If you encounter issues:

1. 📋 Check the log files for error details
2. 🐛 Enable debug mode for verbose output  
3. 🧪 Test with dry run mode first
4. 🔧 Verify mount point manually using system commands
5. 📧 Test email configuration with `--test-smtp`

---

**Made with ❤️ for Plex server administrators**
