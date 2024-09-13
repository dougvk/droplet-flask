# Droplet Instructions

This document provides step-by-step instructions to set up a DigitalOcean Droplet that runs your app, starts automatically on boot, and destroys itself after 60 minutes of inactivity to save costs. The setup does not require Docker and includes a self-destruction script with verbose logging for debugging.

---

## Overview

We will:

1. **Prepare a Droplet** with your app installed and configured to start on boot.
2. **Implement a self-destruction script** that monitors inactivity and destroys the Droplet after 60 minutes of inactivity.
3. **Create a snapshot** of this configured Droplet.
4. **Create a CLI script** to spin up the Droplet from the snapshot.

---

## Prerequisites

- **DigitalOcean Account** with access to create Droplets and snapshots.
- **DigitalOcean API Token** with appropriate permissions.
- **`doctl` Command-Line Tool** installed and authenticated on your laptop.
- **Your App** ready to be deployed on the Droplet.
- **SSH Key** added to your DigitalOcean account.

---

## Step 1: Prepare the Droplet with Your App and Self-Destruction Script

### 1.1. Create a New Droplet

Use `doctl` to create a new Droplet.

```bash
doctl compute droplet create "setup-droplet" \
  --region nyc3 \
  --size s-1vcpu-1gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys your-ssh-key-id \
  --wait
```

**Notes:**

- Replace `your-ssh-key-id` with the ID of your SSH key on DigitalOcean.
- Replace `nyc3` with your desired region.

---

### 1.2. SSH into the Droplet

```bash
ssh root@your-droplet-ip
```

---

### 1.3. Install Your App

#### 1.3.1. Update the System

```bash
apt update && apt upgrade -y
```

#### 1.3.2. Install Necessary Dependencies

Install any dependencies your app requires.

```bash
apt install -y <list-of-dependencies>
```

#### 1.3.3. Install Your App

**Option A:** Clone from a Git repository.

```bash
apt install -y git
git clone https://github.com/yourusername/yourapp.git /opt/yourapp
```

**Option B:** Transfer files using `scp` or `rsync` from your local machine.

```bash
scp -r /path/to/yourapp root@your-droplet-ip:/opt/yourapp
```

#### 1.3.4. Configure Your App

Navigate to `/opt/yourapp` and perform any necessary configuration.

```bash
cd /opt/yourapp
# Example: Install Python requirements
apt install -y python3-pip
pip3 install -r requirements.txt
```

#### 1.3.5. Test Your App

Ensure that your app runs correctly.

```bash
# Example: Start your app
python3 app.py
```

Access your app via the Droplet's IP to confirm it's working.

---

### 1.4. Set Up Your App to Run on Boot

We'll create a systemd service to manage your app.

#### 1.4.1. Create a Systemd Service File

```bash
nano /etc/systemd/system/yourapp.service
```

**Add the following content:**

```ini
[Unit]
Description=Your App Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/yourapp
ExecStart=/usr/bin/python3 /opt/yourapp/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Notes:**

- Replace `/usr/bin/python3 /opt/yourapp/app.py` with the command to start your app.
- Ensure the paths match where your app is located.

#### 1.4.2. Enable and Start the Service

```bash
systemctl enable yourapp.service
systemctl start yourapp.service
```

#### 1.4.3. Verify the Service is Running

```bash
systemctl status yourapp.service
```

Ensure the service is active and running without errors.

---

### 1.5. Implement the Self-Destruction Script

We'll create a script that monitors for network inactivity and destroys the Droplet after 60 minutes of inactivity, with verbose logging for debugging.

#### 1.5.1. Install Required Packages

```bash
apt install -y curl
```

#### 1.5.2. Create the Self-Destruction Script

Create a script at `/usr/local/bin/self_destruct.sh`.

```bash
nano /usr/local/bin/self_destruct.sh
```

**Add the following content:**

```bash
#!/bin/bash

# self_destruct.sh

# Configuration
API_TOKEN="your-limited-scope-api-token"
DROPLET_ID=$(curl -s http://169.254.169.254/metadata/v1/id)
THRESHOLD_MINUTES=60     # Inactivity threshold
CHECK_INTERVAL=5         # Interval between checks (in minutes)
APP_PORT=80              # Replace with your app's port

# Logging setup
LOG_FILE="/var/log/self_destruct.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Self-destruction script started."

# Get Droplet startup time
START_TIME=$(date +%s)

# Initialize last active time to startup time
LAST_ACTIVE=$START_TIME

while true; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Checking for active connections on port $APP_PORT."

  # Check for active connections on the specified port
  CONNECTIONS=$(netstat -an | grep ":$APP_PORT " | grep ESTABLISHED)

  if [ -n "$CONNECTIONS" ]; then
    LAST_ACTIVE=$(date +%s)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Active connections detected. Resetting inactivity timer."
  else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No active connections."
  fi

  # Calculate inactivity duration
  CURRENT_TIME=$(date +%s)
  INACTIVE_SECONDS=$((CURRENT_TIME - LAST_ACTIVE))
  INACTIVE_MINUTES=$((INACTIVE_SECONDS / 60))

  echo "$(date '+%Y-%m-%d %H:%M:%S') - Inactive for $INACTIVE_MINUTES minutes."

  if [ "$INACTIVE_MINUTES" -ge "$THRESHOLD_MINUTES" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Inactivity threshold reached. Destroying Droplet ID $DROPLET_ID."

    # Call DigitalOcean API to destroy the Droplet
    RESPONSE=$(curl -s -X DELETE \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $API_TOKEN" \
      "https://api.digitalocean.com/v2/droplets/$DROPLET_ID")

    if [ -z "$RESPONSE" ]; then
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Droplet destruction initiated successfully."
    else
      echo "$(date '+%Y-%m-%d %H:%M:%S') - Error destroying Droplet: $RESPONSE"
    fi

    exit 0
  else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Droplet will be checked again in $CHECK_INTERVAL minutes."
  fi

  sleep "${CHECK_INTERVAL}m"
done
```

**Important Notes:**

- **API_TOKEN:** Replace `"your-limited-scope-api-token"` with your actual API token, which should have limited permissions.
- **APP_PORT:** Replace `80` with the port your app listens on if different.

#### 1.5.3. Secure the Script and Token

```bash
chmod 700 /usr/local/bin/self_destruct.sh
chown root:root /usr/local/bin/self_destruct.sh
```

#### 1.5.4. Create a Systemd Service for the Self-Destruction Script

```bash
nano /etc/systemd/system/self_destruct.service
```

**Add the following content:**

```ini
[Unit]
Description=Self-Destruction Script
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/self_destruct.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 1.5.5. Enable and Start the Service

```bash
systemctl enable self_destruct.service
systemctl start self_destruct.service
```

#### 1.5.6. Verify the Service is Running

```bash
systemctl status self_destruct.service
```

Ensure the service is active and running.

---

### 1.6. Clean Up and Prepare for Snapshot

- Remove any temporary files or data you don't want in the snapshot.
- Double-check that your app and self-destruction scripts are functioning correctly.

---

## Step 2: Create a Snapshot of the Configured Droplet

### 2.1. Power Off the Droplet

It's a good practice to power off the Droplet before taking a snapshot.

```bash
shutdown -h now
```

---

### 2.2. Take a Snapshot

From your laptop or any machine with `doctl`:

```bash
doctl compute droplet-action snapshot setup-droplet --snapshot-name your-app-snapshot --wait
```

### 2.3. Destroy the Setup Droplet

```bash
doctl compute droplet delete setup-droplet --force
```

---

## Step 3: Create a CLI Script to Spin Up the Droplet

Now that you have a snapshot (`your-app-snapshot`), you can create a script to spin up a new Droplet from this snapshot.

### 3.1. Create the `start_app.sh` Script

```bash
nano start_app.sh
```

**Add the following content:**

```bash
#!/bin/bash

# start_app.sh

# Configuration
DROPLET_NAME="your-droplet-name-$(date +%s)"
REGION="nyc3"
SIZE="s-1vcpu-1gb"
IMAGE="your-app-snapshot"
SSH_KEYS=$(doctl compute ssh-key list --format ID --no-header | paste -sd "," -)

# Create Droplet
doctl compute droplet create "$DROPLET_NAME" \
  --region "$REGION" \
  --size "$SIZE" \
  --image "$IMAGE" \
  --ssh-keys "$SSH_KEYS" \
  --wait

# Retrieve Droplet IP
DROPLET_IP=$(doctl compute droplet get "$DROPLET_NAME" --format PublicIPv4 --no-header)

echo "Droplet '$DROPLET_NAME' has been created with IP: $DROPLET_IP"
echo "Your app should be accessible shortly."
```

**Notes:**

- Replace `your-app-snapshot` with the name of your snapshot.
- Replace `nyc3` with your desired region.

### 3.2. Make the Script Executable

```bash
chmod +x start_app.sh
```

### 3.3. Usage

Run the script from your laptop:

```bash
./start_app.sh
```

---

## Step 4: Test the Entire Setup

- Run `./start_app.sh` to create a new Droplet.
- Access your app via the Droplet's IP address.
- Ensure that the app is running as expected.
- Let the app sit idle and confirm that the Droplet destroys itself after 60 minutes of inactivity.

---

## Additional Considerations

### Defining "Inactivity"

The self-destruction script monitors for active network connections on port 80 (or your app's port). If no connections are established for 60 minutes, it considers the Droplet inactive.

- **Adjust the Port:** If your app listens on a different port, update the `APP_PORT` variable in the script accordingly.

### Security

- **API Token Security:** Since the API token is stored on the Droplet, ensure it's limited in scope.

  - **Create a Separate Token:** Generate a token specifically for the self-destruction script.
  - **Limit Permissions:** Assign only the necessary permissions (e.g., only Droplet deletion).

- **Script Permissions:** Ensure the self-destruction script and log file have restrictive permissions.

### Cost Management

- **Snapshots Cost Money:** Remember that snapshots incur storage costs (~$0.05 per GB per month).
- **Monitor Droplets:** Regularly check your DigitalOcean account to ensure no unintended resources are running.

### Error Handling

- **Self-Destruction Failures:** If the self-destruction script fails, the Droplet might remain running.

  - **Implement Logging:** The script logs activities to `/var/log/self_destruct.log` for troubleshooting.
  - **Notifications:** Consider adding email or Slack notifications upon failure (advanced).

---

## Advanced Enhancements

### Automate API Token Injection

To avoid hardcoding the API token in the script, you could:

- **Use User Data:** Pass the API token as user data when creating the Droplet.

  - Modify the `start_app.sh` script to include the API token in the Droplet creation command.

  ```bash
  USER_DATA=$(base64 -w 0 <<EOF
  #!/bin/bash
  echo 'API_TOKEN="your-limited-scope-api-token"' > /etc/environment
  EOF
  )

  doctl compute droplet create "$DROPLET_NAME" \
    --region "$REGION" \
    --size "$SIZE" \
    --image "$IMAGE" \
    --ssh-keys "$SSH_KEYS" \
    --user-data "$USER_DATA" \
    --wait
  ```

- **Modify the Self-Destruction Script** to read the API token from `/etc/environment`.

  ```bash
  source /etc/environment
  ```

### Monitoring and Alerts

- **External Logging:** If you need to access logs after the Droplet is destroyed, consider sending logs to an external logging service.
- **Monitoring Tools:** Integrate with monitoring tools like DigitalOcean Monitoring to keep track of Droplet activity.
- **Alerts:** Set up alerts to notify you if Droplets fail to destroy themselves.

---

## Ensuring Robustness

### Testing the Script

#### Immediate Testing

- **Reduce `THRESHOLD_MINUTES`** to a smaller value (e.g., `5`) for testing purposes.
- **Monitor the Logs:**

  ```bash
  tail -f /var/log/self_destruct.log
  ```

- **Simulate Activity:**

  - Access your app to create an active connection.
  - Verify that the script resets the inactivity timer.

#### Preventing Premature Shutdown

- **Verify Initialization:**

  - Confirm that upon startup, the script considers the Droplet "active" for the full threshold period.

### Handling Edge Cases

- **Network Fluctuations:**

  - If network issues cause the app to lose connections temporarily, the script might misinterpret this as inactivity.

  - **Solution:** Consider adding more sophisticated checks, like monitoring application logs or health endpoints.

### Advanced Monitoring

- **Monitor Specific Processes:**

  - Instead of (or in addition to) checking network connections, monitor if the app process is running.

- **Use Heartbeats:**

  - Implement a heartbeat mechanism where the app periodically signals that it's active.

---

## Final Notes

- **Remember to Update the API Token:**

  - Ensure you replace `"your-limited-scope-api-token"` with your actual token.

- **Adjust Thresholds as Needed:**

  - `THRESHOLD_MINUTES` and `CHECK_INTERVAL` can be adjusted based on your requirements.

- **Test Thoroughly:**

  - Before relying on this in production, thoroughly test the script to ensure it behaves as expected.

- **Automate Log Retrieval (Optional):**

  - If you need to access logs after the Droplet is destroyed, consider sending logs to an external logging service.

---

## Summary

By following these instructions, you'll have:

- **A CLI command (`start_app.sh`)** that spins up a Droplet from your snapshot, with your app configured to start automatically on boot.
- **A self-destruction mechanism** that monitors for inactivity and destroys the Droplet after 60 minutes of inactivity, with verbose logging to help you debug and understand its behavior.