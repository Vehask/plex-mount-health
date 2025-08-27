# Plex Mount Health Check Monitor

A robust Python script designed to monitor the health of mounted storage used by Plex media servers. This script performs comprehensive checks on mount points and sends email alerts when issues are detected.

## Features

- **Mount Point Validation**: Checks if mount points exist and are properly mounted
- **Read/Write Testing**: Performs actual file operations to verify mount accessibility
- **Email Notifications**: Configurable email alerts with cooldown periods
- **Comprehensive Logging**: Rotating log files with configurable levels
- **Free Space Monitoring**: Optional disk space threshold monitoring
- **Critical Directory Checking**: Ensures important directories exist
- **Dry Run Mode**: Test functionality without making changes
- **Debug Mode**: Verbose output for troubleshooting
- **Failure Threshold**: Only sends alerts after consecutive failures
- **Flexible Configuration**: All settings controlled via configuration file

## Requirements

- Python 3.6 or higher
- Standard Python libraries (no additional packages required)
- Linux system with `/proc/mounts` support
- SMTP server access for email notifications

## Installation

1. Copy the script files to your Plex VM:
   ```bash
   # Place files in a suitable directory, e.g.:
   sudo mkdir -p /opt/plex-mount-health
   sudo cp plex_mount_health.py /opt/plex-mount-health/
   sudo cp plex_mount_health.conf /opt/plex-mount-health/
   sudo chmod +x /opt/plex-mount-health/plex_mount_health.py
   ```

2. Edit the configuration file:
   ```bash
   sudo nano /opt/plex-mount-health/plex_mount_health.conf
   ```

## Configuration

### Quick Start Configuration

Edit the following essential settings in `plex_mount_health.conf`:

```ini
[Mount Settings]
# Update this to your actual mount path
mount_path = /mnt/your-storage-path

[Logging]
# Choose a suitable log location
log_path = /var/log/plex_mount_health.log

[Email Settings]
# Configure your email settings
smtp_server = smtp.gmail.com
smtp_username = your_email@gmail.com
smtp_password = your_app_password
from_email = your_email@gmail.com
to_emails = admin@yourdomain.com

[Email Test Settings]
# Enable test email on startup (optional)
send_test_email_on_startup = false
```

### Complete Configuration Options

#### Mount Settings
- `mount_path`: Path to the mounted storage (required)
- `mount_timeout`: Timeout for mount operations in seconds (default: 30)
- `test_file`: Name of test file created during health checks
- `check_interval`: Seconds between health checks in continuous mode (default: 300)

#### Logging
- `log_path`: Path to log file (default: /var/log/plex_mount_health.log)
- `log_level`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `max_log_size`: Maximum log size in MB before rotation (default: 10)
- `log_backup_count`: Number of backup log files to keep (default: 5)

#### Script Behavior
- `debug`: Enable verbose output (true/false)
- `dry_run`: Simulate actions without making changes (true/false)
- `max_failures`: Consecutive failures before sending alert (default: 3)
- `email_cooldown`: Seconds between email alerts (default: 3600)

#### Email Settings
- `email_enabled`: Enable/disable email notifications (true/false)
- `smtp_server`: SMTP server hostname
- `smtp_port`: SMTP server port (default: 587)
- `smtp_use_tls`: Use TLS encryption (true/false)
- `smtp_username`: SMTP authentication username
- `smtp_password`: SMTP authentication password
- `from_email`: Sender email address
- `to_emails`: Comma-separated list of recipient emails
- `email_subject_prefix`: Prefix for email subjects

#### Email Test Settings
- `send_test_email_on_startup`: Send test email when starting continuous monitoring (true/false)
- `test_email_interval_hours`: Send periodic test emails every N hours (0 to disable)
- `test_email_subject`: Custom subject for test emails
- `test_email_body`: Custom body for test emails

#### Advanced Settings
- `required_mount_options`: Comma-separated mount options to verify
- `check_processes`: Check for processes using the mount (true/false)
- `critical_directories`: Comma-separated list of required directories

## Usage

### Command Line Options

```bash
# Run a single check and exit
python3 plex_mount_health.py --once

# Run with custom configuration file
python3 plex_mount_health.py -c /path/to/custom.conf

# Run continuous monitoring (default)
python3 plex_mount_health.py

# Send test email (uses config file test email settings)
python3 plex_mount_health.py --test-email

# Show help
python3 plex_mount_health.py --help
```

### Running as a Service

Create a systemd service for continuous monitoring:

1. Create service file:
   ```bash
   sudo nano /etc/systemd/system/plex-mount-health.service
   ```

2. Add service configuration:
   ```ini
   [Unit]
   Description=Plex Mount Health Monitor
   After=network.target
   Wants=network.target

   [Service]
   Type=simple
   User=root
   Group=root
   WorkingDirectory=/opt/plex-mount-health
   ExecStart=/usr/bin/python3 /opt/plex-mount-health/plex_mount_health.py
   Restart=always
   RestartSec=30

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable plex-mount-health.service
   sudo systemctl start plex-mount-health.service
   ```

4. Check service status:
   ```bash
   sudo systemctl status plex-mount-health.service
   ```

### Running with Cron

For periodic checks instead of continuous monitoring:

```bash
# Edit crontab
crontab -e

# Add entry to run every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/plex-mount-health/plex_mount_health.py --once
```

## Health Checks Performed

1. **Mount Existence**: Verifies the mount path exists and is actually mounted
2. **Mount Accessibility**: Tests read and write permissions
3. **Read/Write Test**: Creates, writes, reads, and deletes a test file
4. **Critical Directories**: Verifies important directories exist (if configured)

## Email Configuration

### Email Setup Options

#### Option 1: External SMTP Provider (Recommended)
Use Gmail, Outlook, or your ISP's SMTP server:

```ini
[Email Settings]
# Gmail example
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_use_tls = true
smtp_username = your_email@gmail.com
smtp_password_file = /opt/plex-mount-health/.email_password
from_email = your_email@gmail.com
to_emails = admin@yourdomain.com

# Outlook example
smtp_server = smtp-mail.outlook.com
smtp_port = 587
smtp_use_tls = true
smtp_username = your_email@outlook.com
smtp_password_file = /opt/plex-mount-health/.email_password
```

#### Option 2: Install Local Mail Server in VM
Install and configure a mail server like Postfix in the VM:
```bash
sudo apt-get update
sudo apt-get install postfix mailutils
```

Then configure for local relay:
```ini
[Email Settings]
smtp_server = localhost
smtp_port = 25
smtp_use_tls = false
smtp_username =
smtp_password =
from_email = plex@yourdomain.com
to_emails = admin@yourdomain.com
```

### Secure Password Configuration

For security, store email passwords in a separate file instead of the config file:

```bash
# Create secure password file
echo "your_email_password" | sudo tee /opt/plex-mount-health/.email_password

# Secure the file permissions
sudo chmod 600 /opt/plex-mount-health/.email_password
sudo chown root:root /opt/plex-mount-health/.email_password
```

Configure the password file path in your config:
```ini
[Email Settings]
smtp_password_file = /opt/plex-mount-health/.email_password
# smtp_password = # Leave this commented out for security
```

### Email Notifications

The script sends email alerts when:
- Mount health checks fail
- The failure threshold is reached (configurable)
- Cooldown period has elapsed since last alert
- Test emails (if configured)

Email content includes:
- Timestamp and hostname
- Detailed failure information
- Results of all health checks

### Test Email Features

- **Manual Test**: Use `--test-email` parameter to send a test email
- **Startup Test**: Configure `send_test_email_on_startup = true` to verify email on service start
- **Periodic Tests**: Set `test_email_interval_hours` to send regular test emails
- **Custom Test Messages**: Configure custom subject and body for test emails

## Logging

All activities are logged with timestamps:
- Successful health checks
- Failure details
- Email notifications sent
- Configuration errors
- System errors

Log files are automatically rotated when they reach the configured size limit.

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure the script runs with appropriate permissions
   - Check mount point ownership and permissions

2. **Email Authentication Errors**
   - Use app passwords for Gmail accounts
   - Verify SMTP server settings
   - Check firewall rules for SMTP ports

3. **Mount Detection Issues**
   - Verify mount path is correct
   - Check if mount is actually mounted: `mount | grep your-path`
   - Ensure `/proc/mounts` is accessible

4. **Test File Creation Failures**
   - Check write permissions on mount point
   - Verify sufficient disk space
   - Ensure mount is not read-only


### Debug Mode

Enable debug mode in the configuration:
```ini
[Script Behavior]
debug = true
```

This provides verbose output showing:
- Configuration values loaded
- Each health check step
- Detailed error messages

### Dry Run Mode

Test the script without making changes:
```ini
[Script Behavior]
dry_run = true
```

This simulates all operations without:
- Creating test files
- Sending actual emails
- Making any modifications

## Security Considerations

- Store the configuration file with restricted permissions: `chmod 600 plex_mount_health.conf`
- **Use password files instead of storing passwords in config**: `smtp_password_file`
- Use app passwords for Gmail instead of main account passwords
- Secure password files: `chmod 600` and `chown root:root`
- Regularly rotate email passwords
- Review log files for security events

## Version History

- **v1.0**: Initial release with comprehensive mount health checking

## Support

For issues or questions:
1. Check the log files for error details
2. Enable debug mode for verbose output
3. Test with dry run mode first
4. Verify mount point manually using system commands

## License

This script is provided as-is for use with Plex media servers. Modify as needed for your environment.#   p l e x - m o u n t - h e a l t h  
 