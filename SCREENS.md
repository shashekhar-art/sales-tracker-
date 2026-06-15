# Bishwa Medicare — screen-by-screen tour

A one-page tour of every page in the Flask UI and what you can do there. Sign in first at `http://127.0.0.1:5000/login`.

## Auth

| URL | Page | What you see |
|---|---|---|
| `/login` | Sign in | Username/email + password. "Create an account" link goes to `/register`. |
| `/register` | Sign up | Self-serve account creation — writes to the `employees` table, role = `employee`, auto-logs you in. |
| `/logout` | — | Clears session, sends you back to `/login`. |

## Employee day

| URL | Page | What you see |
|---|---|---|
| `/dashboard` | Home | Today's plan (if declared), check-in card with the **address-first** location flow, period summary (`D · C · S · R · W` counts), latest activity. |
| `/plan` | Plan today | Single address field + "Use my current location" + filter chips for all 5 account types + multi-select picker for the day's accounts. |
| `/visit` | Log visit | Pick an account → enter address (or auto-fill) → outcome → notes → **proof selfie (new)** → submit. "Today's visits" table below shows what you've logged so far, with thumbnail. |
| `/history` | History | Past 200 check-ins / visits with planned vs actual, distance, **selfie thumbnail (new)**, match badge. |
| `/accounts` | Accounts directory | Search + filter chips by type (all 5 visible) + by district. |
| `/accounts/add` | Add account | Name + type dropdown (all 5) + district + address + lat/lon. |
| `/accounts/<id>/edit` | Edit account | Same form pre-filled. |
| `/reports` | Reports | Bar chart visits-by-type with all 5 bars (Doctors / Chemists / Stockists / Retailers / Wholesalers). |

## Admin / proctor (admin role only)

| URL | Page | What you see |
|---|---|---|
| `/admin` | Admin home | Create new employee form + list of all employees, today's plan per employee, recent anomaly flags. |
| `/proctor` | All India | Per-region rollups (visits today / week / month, achievement %). |
| `/proctor/region/<id>` | Region detail | District-level rollups inside the region. |
| `/proctor/district/<id>` | District detail | Per-employee rollups inside the district. |
| `/proctor/employee/<id>` | Employee detail | One employee's last 25 visits, anomaly flags, period stats with all 5 type counts. |

## The selfie flow (visit page)

1. Click **Open camera** in the "Proof selfie" block.
2. Browser asks for camera permission → allow.
3. Live preview appears in the square frame.
4. Click **Capture** → still image freezes in the frame, and is attached to the form as `selfie-{timestamp}.jpg`.
5. Submit the form. The JPEG is saved to `static/uploads/selfies/{employee_id}/` and the path is stored on the `checkins` row.
6. The thumbnail appears in the "Today's visits" table and in `/history`. Click the thumbnail to open the full-size image.

## Location flow (plan / dashboard / visit)

1. Type the address freely, or click **Use my current location**.
2. Browser asks for location permission → allow.
3. GPS coords are read, then `/api/reverse_geocode?lat=&lon=` returns a human-readable address.
4. Address field auto-fills. You can still edit it.
5. Status line under the button: ✅ success / ⚠️ partial / ❌ error. Hard failures also show an alert popup so you can't miss it.
