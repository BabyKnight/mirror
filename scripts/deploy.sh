#!/bin/bash
#
# A script to configure and deploy a Django project with Gunicorn and Nginx.
#
# This script performs the following actions:
# 1. Creates a Gunicorn systemd service file.
# 2. Creates an Nginx site configuration file.
# 3. Enables and starts the services.
#
# Please make sure to run this script with sudo.

# --- Configuration Variables ---
# Modify these variables to match your setup
PROJECT_USER=$(whoami)
PROJECT_GROUP=$PROJECT_USER

SCRIPTS_DIR=$(dirname $(readlink -f "$0"))
PROJECT_DIR=$(dirname $SCRIPTS_DIR)
VIRTUALENV_DIR="${PROJECT_DIR}/environ"

DJANGO_PROJECT_DIR="${PROJECT_DIR}/mirror"
DJANGO_APP_NAME="config"

GUNICORN_SOCK_PATH="/tmp/linux_automation.sock"
GUNICORN_SERVICE_NAME="gunicorn_linux_automation.service"
NGINX_CONF_NAME="linux_automation.conf"


DJANGO_STATIC_ROOT="${DJANGO_PROJECT_DIR}/staticfiles"

YOUR_DOMAIN="_" # Replace with your domain or IP

# --- Step 1: Create Gunicorn Systemd Service File ---
echo "Creating Gunicorn systemd service file..."

sudo cat > /etc/systemd/system/${GUNICORN_SERVICE_NAME} << EOL
[Unit]
Description=Gunicorn instance to serve the 'Linux automation' project
After=network.target

[Service]
User=${PROJECT_USER}
# IMPORTANT: Use the group for the web server (e.g., www-data or nginx) to avoid permission issues.
Group=www-data
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONPATH=${DJANGO_PROJECT_DIR}
ExecStart=${VIRTUALENV_DIR}/bin/gunicorn --workers 3 --bind unix:${GUNICORN_SOCK_PATH} mirror.${DJANGO_APP_NAME}.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
UMask=007

# Standard output and error logs
StandardOutput=append:${PROJECT_DIR}/logs/gunicorn_access.log
StandardError=append:${PROJECT_DIR}/logs/gunicorn_error.log

[Install]
WantedBy=multi-user.target
EOL

echo "Gunicorn service file created at /etc/systemd/system/${GUNICORN_SERVICE_NAME}"

# --- Step 2: Reload and Start Gunicorn Service ---
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Starting and enabling Gunicorn service..."
sudo systemctl start ${GUNICORN_SERVICE_NAME}
sudo systemctl enable ${GUNICORN_SERVICE_NAME}

echo "Gunicorn service has been started. You can check its status with: sudo systemctl status ${GUNICORN_SERVICE_NAME}"


# --- Step 3: Create Nginx Configuration File ---
echo "Creating Nginx configuration file..."

sudo cat > /etc/nginx/sites-available/${NGINX_CONF_NAME} << EOL
server {
    listen 80 default_server;
    server_name ${YOUR_DOMAIN};

    access_log /var/log/nginx/linux_automation_access.log;
    error_log /var/log/nginx/linux_automation_error.log;

    location /static/ {
        alias ${DJANGO_STATIC_ROOT}/;
        expires 1y;
    }

    location / {
        proxy_pass http://unix:${GUNICORN_SOCK_PATH}:/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOL

echo "Nginx configuration file created at /etc/nginx/sites-available/${NGINX_CONF_NAME}"

# --- Step 4: Enable and Restart Nginx Service ---
echo "Creating symlink to enable the site..."
sudo ln -s /etc/nginx/sites-available/${NGINX_CONF_NAME} /etc/nginx/sites-enabled/

echo "Testing Nginx configuration..."
sudo nginx -t

echo "Restarting Nginx service..."
sudo systemctl restart nginx

echo "Nginx has been restarted. Your Django site should now be live."

echo "Deployment script finished."
