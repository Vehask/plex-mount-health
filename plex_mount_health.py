#!/usr/bin/env python3
"""
Plex Mount Health Check Script
==============================

This script monitors the health of mounted storage used by Plex media server.
It checks for mount availability, performs read/write tests, and sends email
alerts when issues are detected.

Author: Plex Mount Health Monitor
Version: 1.0
"""

import os
import sys
import time
import logging
import logging.handlers
import configparser
import smtplib
import subprocess
import shutil
import tempfile
import argparse
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import psutil


class PlexMountHealthChecker:
    def __init__(self, config_file='plex_mount_health.conf'):
        """Initialize the mount health checker with configuration."""
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.logger = None
        self.last_email_sent = None
        self.last_test_email_sent = None
        self.consecutive_failures = 0
        
        # Load configuration
        self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Load configuration from the config file."""
        if not os.path.exists(self.config_file):
            print(f"ERROR: Configuration file '{self.config_file}' not found!")
            sys.exit(1)
            
        try:
            self.config.read(self.config_file)
        except Exception as e:
            print(f"ERROR: Failed to read configuration file: {e}")
            sys.exit(1)
            
        # Validate required sections
        required_sections = ['Mount Settings', 'Logging', 'Script Behavior', 'Email Settings']
        for section in required_sections:
            if section not in self.config:
                print(f"ERROR: Missing required section '{section}' in config file")
                sys.exit(1)
    
    def get_config_value(self, section, key, default=None, value_type=str):
        """Get configuration value with type conversion and default fallback."""
        try:
            if value_type == bool:
                return self.config.getboolean(section, key)
            elif value_type == int:
                return self.config.getint(section, key)
            elif value_type == float:
                return self.config.getfloat(section, key)
            else:
                return self.config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError, ValueError):
            if default is not None:
                return default
            raise
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_path = self.get_config_value('Logging', 'log_path', '/var/log/plex_mount_health.log')
        log_level = self.get_config_value('Logging', 'log_level', 'INFO')
        max_log_size = self.get_config_value('Logging', 'max_log_size', 10, int) * 1024 * 1024  # Convert MB to bytes
        log_backup_count = self.get_config_value('Logging', 'log_backup_count', 5, int)
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('PlexMountHealth')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=max_log_size, backupCount=log_backup_count
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for debug mode
        if self.get_config_value('Script Behavior', 'debug', False, bool):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log_and_print(self, level, message):
        """Log message and print if in debug mode."""
        getattr(self.logger, level)(message)
        if self.get_config_value('Script Behavior', 'debug', False, bool):
            print(f"{level.upper()}: {message}")
    
    def check_mount_exists(self, mount_path):
        """Check if the mount point exists and is actually mounted."""
        try:
            if not os.path.exists(mount_path):
                return False, f"Mount path '{mount_path}' does not exist"
            
            if not os.path.ismount(mount_path):
                # Additional check using /proc/mounts
                with open('/proc/mounts', 'r') as f:
                    mounts = f.read()
                    if mount_path not in mounts:
                        return False, f"'{mount_path}' is not mounted"
            
            return True, "Mount point exists and is mounted"
        except Exception as e:
            return False, f"Error checking mount: {str(e)}"
    
    def check_mount_accessibility(self, mount_path):
        """Check if the mount is accessible (readable/writable)."""
        try:
            # Check read access
            if not os.access(mount_path, os.R_OK):
                return False, f"Mount '{mount_path}' is not readable"
            
            # Check write access
            if not os.access(mount_path, os.W_OK):
                return False, f"Mount '{mount_path}' is not writable"
            
            return True, "Mount is accessible for read/write operations"
        except Exception as e:
            return False, f"Error checking mount accessibility: {str(e)}"
    
    def perform_read_write_test(self, mount_path):
        """Perform a read/write test on the mount."""
        test_dir = os.path.join(mount_path, '.health_check')
        test_file = self.get_config_value('Mount Settings', 'test_file', 'health_check.tmp')
        test_file_path = os.path.join(test_dir, test_file)
        
        try:
            # Create test directory if it doesn't exist
            if not os.path.exists(test_dir):
                if not self.get_config_value('Script Behavior', 'dry_run', False, bool):
                    os.makedirs(test_dir, exist_ok=True)
                else:
                    self.log_and_print('info', f"DRY RUN: Would create directory '{test_dir}'")
            
            # Write test
            test_content = f"Health check test - {datetime.now().isoformat()}"
            if not self.get_config_value('Script Behavior', 'dry_run', False, bool):
                with open(test_file_path, 'w') as f:
                    f.write(test_content)
                
                # Read test
                with open(test_file_path, 'r') as f:
                    read_content = f.read()
                
                if read_content != test_content:
                    return False, "Read/write test failed: content mismatch"
                
                # Clean up
                os.remove(test_file_path)
            else:
                self.log_and_print('info', f"DRY RUN: Would write/read test file '{test_file_path}'")
            
            return True, "Read/write test successful"
        except Exception as e:
            return False, f"Read/write test failed: {str(e)}"
    
    
    def check_critical_directories(self, mount_path):
        """Check if critical directories exist in the mount."""
        critical_dirs = self.get_config_value('Advanced Settings', 'critical_directories', '')
        
        if not critical_dirs.strip():
            return True, "No critical directories configured"
        
        missing_dirs = []
        for dir_name in [d.strip() for d in critical_dirs.split(',') if d.strip()]:
            dir_path = os.path.join(mount_path, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            return False, f"Missing critical directories: {', '.join(missing_dirs)}"
        
        return True, "All critical directories exist"
    
    def check_mount_health(self):
        """Perform comprehensive mount health check."""
        mount_path = self.get_config_value('Mount Settings', 'mount_path')
        self.log_and_print('info', f"Starting mount health check for: {mount_path}")
        
        checks = [
            ("Mount Existence", self.check_mount_exists),
            ("Mount Accessibility", self.check_mount_accessibility),
            ("Read/Write Test", self.perform_read_write_test),
            ("Critical Directories", self.check_critical_directories)
        ]
        
        all_passed = True
        results = []
        
        for check_name, check_func in checks:
            try:
                passed, message = check_func(mount_path)
                results.append(f"{check_name}: {'PASS' if passed else 'FAIL'} - {message}")
                
                if passed:
                    self.log_and_print('info', f"{check_name}: PASS - {message}")
                else:
                    self.log_and_print('error', f"{check_name}: FAIL - {message}")
                    all_passed = False
                    
            except Exception as e:
                error_msg = f"Exception during {check_name}: {str(e)}"
                results.append(f"{check_name}: ERROR - {error_msg}")
                self.log_and_print('error', error_msg)
                all_passed = False
        
        return all_passed, results
    
    def should_send_email(self):
        """Check if we should send an email based on cooldown period."""
        if not self.get_config_value('Email Settings', 'email_enabled', True, bool):
            return False
        
        email_cooldown = self.get_config_value('Script Behavior', 'email_cooldown', 3600, int)
        
        if self.last_email_sent is None:
            return True
        
        time_since_last = datetime.now() - self.last_email_sent
        return time_since_last.total_seconds() >= email_cooldown
    
    def send_email_alert(self, subject, body, is_test=False):
        """Send email alert about mount issues."""
        if not self.get_config_value('Email Settings', 'email_enabled', True, bool):
            self.log_and_print('info', "Email notifications disabled")
            return False
        
        if not is_test and not self.should_send_email():
            self.log_and_print('info', "Email cooldown period active, skipping email")
            return False
        
        if self.get_config_value('Script Behavior', 'dry_run', False, bool):
            self.log_and_print('info', f"DRY RUN: Would send email with subject '{subject}'")
            return True
        
        try:
            # Email configuration
            smtp_server = self.get_config_value('Email Settings', 'smtp_server')
            smtp_port = self.get_config_value('Email Settings', 'smtp_port', 587, int)
            smtp_use_tls = self.get_config_value('Email Settings', 'smtp_use_tls', True, bool)
            smtp_username = self.get_config_value('Email Settings', 'smtp_username')
            
            # Get password from file or config
            smtp_password = self.get_email_password()
            
            from_email = self.get_config_value('Email Settings', 'from_email')
            to_emails = self.get_config_value('Email Settings', 'to_emails')
            subject_prefix = self.get_config_value('Email Settings', 'email_subject_prefix', '[Plex Mount Alert]')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_emails
            
            # Use different prefix for test emails
            if is_test:
                msg['Subject'] = f"[Plex Mount Test] {subject}"
            else:
                msg['Subject'] = f"{subject_prefix} {subject}"
            
            # Add timestamp and hostname to body
            hostname = os.uname().nodename
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_body = f"Timestamp: {timestamp}\nHostname: {hostname}\n\n{body}"
            
            msg.attach(MIMEText(full_body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            if is_test:
                self.last_test_email_sent = datetime.now()
                self.log_and_print('info', f"Test email sent successfully to: {to_emails}")
            else:
                self.last_email_sent = datetime.now()
                self.log_and_print('info', f"Email alert sent successfully to: {to_emails}")
            return True
            
        except Exception as e:
            email_type = "test email" if is_test else "email alert"
            self.log_and_print('error', f"Failed to send {email_type}: {str(e)}")
            return False
    
    def get_email_password(self):
        """Get email password from file or config."""
        # Try password file first (recommended)
        password_file = self.get_config_value('Email Settings', 'smtp_password_file', '', str)
        if password_file and os.path.exists(password_file):
            try:
                with open(password_file, 'r') as f:
                    password = f.read().strip()
                if password:
                    return password
            except Exception as e:
                self.log_and_print('error', f"Failed to read password file '{password_file}': {e}")
        
        # Fallback to config file password
        return self.get_config_value('Email Settings', 'smtp_password', '', str)
    
    def test_smtp_connection(self):
        """Test SMTP connection without sending email."""
        print("Testing SMTP connection...")
        
        try:
            # Email configuration
            smtp_server = self.get_config_value('Email Settings', 'smtp_server')
            smtp_port = self.get_config_value('Email Settings', 'smtp_port', 587, int)
            smtp_use_tls = self.get_config_value('Email Settings', 'smtp_use_tls', True, bool)
            smtp_username = self.get_config_value('Email Settings', 'smtp_username')
            smtp_password = self.get_email_password()
            
            print(f"SMTP Server: {smtp_server}")
            print(f"SMTP Port: {smtp_port}")
            print(f"Use TLS: {smtp_use_tls}")
            print(f"Username: {smtp_username}")
            print(f"Password: {'*' * len(smtp_password) if smtp_password else '(empty)'}")
            
            # Test connection
            print("\n1. Testing DNS resolution...")
            import socket
            try:
                ip = socket.gethostbyname(smtp_server)
                print(f"   ✓ DNS resolved: {smtp_server} -> {ip}")
            except socket.gaierror as e:
                print(f"   ✗ DNS resolution failed: {e}")
                return False
            
            print("2. Testing SMTP connection...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            print(f"   ✓ Connected to {smtp_server}:{smtp_port}")
            
            if smtp_use_tls:
                print("3. Testing TLS...")
                server.starttls()
                print("   ✓ TLS established")
            
            if smtp_username and smtp_password:
                print("4. Testing authentication...")
                server.login(smtp_username, smtp_password)
                print("   ✓ Authentication successful")
            
            server.quit()
            print("\n✓ SMTP connection test PASSED")
            return True
            
        except Exception as e:
            print(f"\n✗ SMTP connection test FAILED: {str(e)}")
            print("\nTroubleshooting tips:")
            print("1. Check if SMTP server address is correct (no http:// prefix)")
            print("2. Verify SMTP port (usually 25, 587, or 465)")
            print("3. Check if authentication is required")
            print("4. For Gmail, use app passwords instead of regular password")
            print("5. Check firewall settings")
            return False
    
    def send_test_email(self):
        """Send a test email using configuration settings."""
        subject = self.get_config_value('Email Test Settings', 'test_email_subject', 'Test Email from Plex Mount Health Monitor')
        body = self.get_config_value('Email Test Settings', 'test_email_body', 'This is a test email to verify the Plex Mount Health Monitor email functionality is working correctly.')
        return self.send_email_alert(subject, body, is_test=True)
    
    def should_send_periodic_test_email(self):
        """Check if we should send a periodic test email."""
        test_interval_hours = self.get_config_value('Email Test Settings', 'test_email_interval_hours', 0, int)
        
        if test_interval_hours <= 0:
            return False
        
        if self.last_test_email_sent is None:
            return True
        
        time_since_last = datetime.now() - self.last_test_email_sent
        return time_since_last.total_seconds() >= (test_interval_hours * 3600)
    
    def run_single_check(self):
        """Run a single health check and handle results."""
        try:
            all_passed, results = self.check_mount_health()
            
            if all_passed:
                self.consecutive_failures = 0
                self.log_and_print('info', "Mount health check PASSED")
                return True
            else:
                self.consecutive_failures += 1
                max_failures = self.get_config_value('Script Behavior', 'max_failures', 3, int)
                
                self.log_and_print('warning', f"Mount health check FAILED (failure #{self.consecutive_failures})")
                
                # Send alert if we've reached the failure threshold
                if self.consecutive_failures >= max_failures:
                    subject = f"Mount Health Check Failed ({self.consecutive_failures} consecutive failures)"
                    body = "The following mount health checks failed:\n\n" + "\n".join(results)
                    self.send_email_alert(subject, body)
                
                return False
                
        except Exception as e:
            self.log_and_print('error', f"Unexpected error during health check: {str(e)}")
            return False
    
    def run_continuous(self):
        """Run continuous health checking with configured interval."""
        check_interval = self.get_config_value('Mount Settings', 'check_interval', 300, int)
        
        self.log_and_print('info', f"Starting continuous mount health monitoring (interval: {check_interval}s)")
        
        # Send startup test email if configured
        if self.get_config_value('Email Test Settings', 'send_test_email_on_startup', False, bool):
            self.log_and_print('info', "Sending startup test email...")
            self.send_test_email()
        
        try:
            while True:
                self.run_single_check()
                
                # Check if we should send periodic test email
                if self.should_send_periodic_test_email():
                    self.log_and_print('info', "Sending periodic test email...")
                    self.send_test_email()
                
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.log_and_print('info', "Mount health monitoring stopped by user")
        except Exception as e:
            self.log_and_print('error', f"Fatal error in continuous monitoring: {str(e)}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Plex Mount Health Check Monitor')
    parser.add_argument('-c', '--config', default='plex_mount_health.conf',
                       help='Path to configuration file (default: plex_mount_health.conf)')
    parser.add_argument('--once', action='store_true',
                       help='Run a single check and exit')
    parser.add_argument('--test-email', action='store_true',
                       help='Send a test email and exit')
    parser.add_argument('--test-smtp', action='store_true',
                       help='Test SMTP connection without sending email')
    
    args = parser.parse_args()
    
    try:
        checker = PlexMountHealthChecker(args.config)
        
        if args.test_smtp:
            checker.test_smtp_connection()
        elif args.test_email:
            checker.send_test_email()
        elif args.once:
            success = checker.run_single_check()
            sys.exit(0 if success else 1)
        else:
            checker.run_continuous()
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()