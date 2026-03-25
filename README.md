# Whatapp

Whatapp is a Frappe app that provides a desk UI for the Go WhatsApp multi-device service from `aldinokemal/go-whatsapp-web-multidevice`.

Current app version: `0.3.0`

## Features

- Run GoWA locally inside the same bench environment without Docker
- Connect Frappe to a local or external GoWA REST service
- Manage devices and pairing flows from Desk
- Browse chats and recent messages
- Send text messages from a Frappe UI frontend
- Receive GoWA webhooks with HMAC verification
- Forward eligible Frappe `Notification Log` entries to WhatsApp
- Store outbound WhatsApp delivery attempts in `Whatapp Message Log`
- Send direct WhatsApp updates for HRMS leave application approval flows
- Send direct WhatsApp updates for ERPNext `Issue` creation and status changes
- Send ad hoc WhatsApp messages directly from `Employee`, `Customer`, `Supplier`, `Lead`, and `Contact` forms
- Manage per-user WhatsApp notification numbers from the Whatapp settings screen
- Read a dedicated `WhatsApp Number` field from the Frappe `User` form as the preferred notification target

## Architecture

This app acts as:

1. A secure Frappe-side configuration and proxy layer
2. A Frappe Desk page powered by Vue 3 and `frappe-ui`
3. A webhook receiver for WhatsApp events forwarded by GoWA
4. A local GoWA bootstrap layer for supported systems
5. A reusable outbound delivery layer with persistent message logging

## What's new in 0.3.0

- Added a shared outbound delivery layer backed by `Whatapp Message Log` for full send auditability
- Added master-data recipient resolution for `Employee`, `Customer`, `Supplier`, `Lead`, `Contact`, and `User`
- Added HRMS `Leave Application` notifications for request, decision, and cancellation events
- Added ERPNext `Issue` notifications for creation and status changes
- Added direct `Send WhatsApp` desk actions on core master forms
- Tightened manual send permissions so users must be able to read the recipient or reference document they are sending from

See `CHANGELOG.md` for the release history and `.github/release-notes/v0.3.0.md` for the GitHub release text.

## Phase 1 delivery foundation

This app now includes a `Whatapp Message Log` DocType for outbound auditability.

Current outbound log statuses:

- `Queued`
- `Sent`
- `Failed`
- `Skipped`

The existing notification forwarding flow writes to this log automatically.
You can also send typed outbound messages programmatically through `whatapp.api.send_event_message`.
`send_event_message` can now resolve recipients directly from master records such as `Employee`, `Customer`, `Supplier`, `Lead`, `Contact`, and `User`.

Manual sending from Desk is also available through a `Send WhatsApp` action on supported master forms. The dialog previews the resolved phone number and source before sending.

HRMS `Leave Application` now also sends direct WhatsApp updates for:

- new leave requests to the approver
- approved or rejected leave decisions to the employee
- leave cancellations to the employee

ERPNext `Issue` now sends direct WhatsApp updates for:

- new support ticket creation
- support ticket status changes

Issue recipients are resolved from the linked master in this order:

- `Customer`
- `Lead`
- `Contact`

Recipient phone resolution priority now follows the master data itself:

- `Employee.cell_number`
- `Lead.whatsapp_no`, then `Lead.mobile_no`, then `Lead.phone`
- `Customer.mobile_no`, then linked `Contact.mobile_no`
- `Supplier.mobile_no`, then linked `Contact.mobile_no`
- `Contact.mobile_no`, then `Contact.phone`
- `User.whatapp_whatsapp_number`, then `User.mobile_no`, then `User.phone`

## Supported local runtime

The app can install and run the GoWA binary locally for these targets:

- Linux `x86_64` / `amd64`
- Linux `arm64` / `aarch64`
- macOS `x86_64`
- macOS `arm64`

The binary is downloaded from the upstream GitHub release during app bootstrap if it is missing.

## System dependencies

Python package dependencies remain unchanged for this release and are declared in `pyproject.toml`:

- `frappe`
- `requests`

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

If the bench has exactly one site, the runner can auto-detect it. On multi-site benches, set `WHATAPP_SITE` explicitly.

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