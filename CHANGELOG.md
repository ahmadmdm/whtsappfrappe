# Changelog

All notable changes to this project will be documented in this file.

## 0.3.0 - 2026-03-25

### Added

- Shared outbound delivery flow with persistent `Whatapp Message Log` entries.
- Master-data recipient resolution for `Employee`, `Customer`, `Supplier`, `Lead`, `Contact`, and `User`.
- HRMS `Leave Application` WhatsApp notifications for submission, approval or rejection, and cancellation.
- ERPNext `Issue` WhatsApp notifications for creation and status changes.
- Direct `Send WhatsApp` desk action on `Employee`, `Customer`, `Supplier`, `Lead`, and `Contact` forms.
- Automated tests for recipient resolution and issue event integrations.

### Changed

- `Notification Log` forwarding now writes through the shared outbound delivery layer.
- Manual send permissions now require access to the recipient or reference document instead of only allowing `System Manager`.
- Whatapp desk asset cache version was refreshed to load the latest frontend changes reliably.
- Direct form sending now shows a clean desk message when the target record has no WhatsApp or mobile number.

### Dependencies

- Python package dependencies remain `frappe` and `requests`.
- Linux media support still depends on system packages such as `ffmpeg` and `webp`.