# Whatapp

Whatapp is a Frappe app that provides a desk UI for the Go WhatsApp multi-device service from `aldinokemal/go-whatsapp-web-multidevice`.

Current app version: `0.2.1`

## Features

- Run GoWA locally inside the same bench environment without Docker
- Connect Frappe to a local or external GoWA REST service
- Manage devices and pairing flows from Desk
- Browse chats and recent messages
- Send text messages from a Frappe UI frontend
- Receive GoWA webhooks with HMAC verification
- Forward eligible Frappe `Notification Log` entries to WhatsApp
- Manage per-user WhatsApp notification numbers from the Whatapp settings screen
- Read a dedicated `WhatsApp Number` field from the Frappe `User` form as the preferred notification target

## Architecture

This app acts as:

1. A secure Frappe-side configuration and proxy layer
2. A Frappe Desk page powered by Vue 3 and `frappe-ui`
3. A webhook receiver for WhatsApp events forwarded by GoWA
4. A local GoWA bootstrap layer for supported systems

## Supported local runtime

The app can install and run the GoWA binary locally for these targets:

- Linux `x86_64` / `amd64`
- Linux `arm64` / `aarch64`
- macOS `x86_64`
- macOS `arm64`

The binary is downloaded from the upstream GitHub release during app bootstrap if it is missing.

## System dependencies

For full media support on Linux, install these packages on the target server:

```bash
sudo apt update
sudo apt install ffmpeg webp
```

Without them, core chat and text messaging still work, but some media workflows may be limited.

## Installation on another bench

### 1. Get the app

```bash
cd /path/to/frappe-bench/apps
git clone https://github.com/ahmadmdm/whtsappfrappe.git whatapp
```

### 2. Install the Python package in the bench env

```bash
cd /path/to/frappe-bench
./env/bin/pip install -e apps/whatapp
```

### 3. Install the app on a site

```bash
bench --site your-site install-app whatapp
bench --site your-site migrate
bench --site your-site clear-cache
```

The install/migrate hooks will:

- create the `Whatapp Settings` defaults
- create the `User.WhatsApp Number` custom field
- generate the local GoWA env file for the site
- download the local GoWA binary if it is missing

## Starting the local GoWA service

If your bench does not already manage background processes for Whatapp, run the local service supervisor with:

```bash
cd /path/to/frappe-bench
WHATAPP_SITE=your-site env/bin/python -m whatapp.local_service_runner
```

Or, if the package script entrypoint is available:

```bash
cd /path/to/frappe-bench
WHATAPP_SITE=your-site env/bin/whatapp-local-service
```

For persistent deployment, run that command under your process manager such as:

- `supervisor`
- `systemd`
- a bench `Procfile` entry

## Local runtime files

The app stores its local runtime under:

- binary: `apps/whatapp/.local/gowa/bin/whatsapp`
- runtime data: `apps/whatapp/.local/gowa/data/`
- site env file: `sites/<site>/private/whatapp/gowa-<site>.env`

## Configuration inside Frappe

After installation:

1. Open `Whatapp Settings`
2. Confirm `Service URL` points to the local service, usually `http://127.0.0.1:8000`
3. Pair a WhatsApp device from the Whatapp desk page
4. Fill `User > WhatsApp Number` for any user who should receive WhatsApp notifications
5. Enable notification forwarding in `Whatapp Settings`

## Notification number source priority

When Whatapp sends a user notification to WhatsApp, it resolves the target number in this order:

1. `Whatapp User Notification Setting.phone_number`
2. `User.whatapp_whatsapp_number` (`WhatsApp Number` field)
3. `User.mobile_no`
4. `User.phone`

## Important deployment note

The app repository can be moved to another server, but the target bench still needs a long-running process for:

- Frappe web
- Redis cache / queue
- the local Whatapp GoWA runner

If you do not add the local runner to your server's process manager, the UI will load but the WhatsApp backend will not be available.

## Optional external mode

If you prefer not to use the bundled local runtime, you can still point `Service URL` to an external GoWA service.

Example Docker command for external mode:

```bash
docker run --detach \
  --publish=3000:3000 \
  --name=whatsapp \
  --restart=always \
  --volume=$(docker volume create --name=whatsapp):/app/storages \
  ghcr.io/aldinokemal/go-whatsapp-web-multidevice \
  rest
```

Then configure the base URL in `Whatapp Settings`.