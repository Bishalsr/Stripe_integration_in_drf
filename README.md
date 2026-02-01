# Stripe Integration in DRF

This project demonstrates integrating Stripe payments with a Django + Django REST Framework (DRF) application.

Repository: [Bishalsr/Stripe_integration_in_drf](https://github.com/Bishalsr/Stripe_integration_in_drf)

## Summary

This repository contains a Django project with:
- REST API endpoints (DRF)
- JWT authentication (Simple JWT)
- Stripe Checkout + webhook handling
- Example account registration and subscription flow
- A Project viewset for basic CRUD
 To get the webhook key write this code in your CLI.
```bash
stripe listen --forward-to localhost:8000/api/stripe/webhook/
```
  

## Requirements

- Python 3.10+ (or the version your project supports)
- pip
- A Stripe account (test keys for development)
- Optional: ngrok for webhook testing

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

At minimum, set:

- `DJANGO_SECRET_KEY`
- `DEBUG` (True/False)
- `STRIPE_SECRET_KEY` (sk_test_... / sk_live_...)
- `STRIPE_PUBLISHABLE_KEY` (pk_test_... / pk_live_...)
- `STRIPE_WEBHOOK_SECRET` (whsec_... from Stripe Dashboard)
- Database settings or `DATABASE_URL` if configured

## API endpoints

All API endpoints live under the project's URL configuration:

- Admin: `GET /admin/`

Top-level API prefixes configured:
- `api/accounts/` → includes account & Stripe endpoints
- `api/projects/` → DRF router for ProjectViewSet
- `api/token/` and `api/token/refresh/` → JWT token endpoints

Detailed endpoints (paths are relative to the server base URL, e.g. `http://localhost:8000`):

- Authentication (JWT)
  - `POST /api/token/`  
    - Obtain JWT access + refresh tokens.  
    - Request body (example): `{"username": "bob", "password": "secret"}`  
    - Response: `{ "access": "...", "refresh": "..." }`
  - `POST /api/token/refresh/`  
    - Refresh access token using the refresh token.  
    - Request body (example): `{"refresh": "<refresh_token>"}`

- Accounts & Stripe
  - `POST /api/accounts/register/`  
    - Register a new user. Uses `RegisterView` (AllowAny).  
    - Typical fields: `username`, `password`, `email` (depends on `accounts.serializers.RegisterSerializer`).
  - `POST /api/accounts/create-checkout/`  
    - Create a Stripe Checkout Session (subscriptions). Requires authentication (JWT).  
    - Request body example: `{"plan": "pro"}` — the view maps `"plan"` to a Stripe price ID.  
    - Response: `{"checkout_url": "<stripe_checkout_url>"}`  
    - Authorization header: `Authorization: Bearer <access_token>`
  - `POST /api/accounts/stripe/webhook/`  
    - Webhook endpoint used by Stripe to POST events. The webhook implementation verifies the Stripe signature using `STRIPE_WEBHOOK_SECRET`.
    - Handles events such as `checkout.session.completed` to create/update a local `Subscription` for the user.
    - This endpoint is CSRF-exempt and meant to be called by Stripe (do not publicly expose the secret).
  - `GET /api/accounts/success/`  
    - Payment success landing endpoint. Accepts `session_id` query param (shown to user after redirect).
  - `GET /api/accounts/cancel/`  
    - Payment canceled landing endpoint.

- Projects (DRF router at `/api/projects/`)
  - `GET /api/projects/` — list projects
  - `POST /api/projects/` — create a project
  - `GET /api/projects/{pk}/` — retrieve a project
  - `PUT /api/projects/{pk}/` — update a project (replace)
  - `PATCH /api/projects/{pk}/` — partial update
  - `DELETE /api/projects/{pk}/` — delete a project

Note: The ProjectViewSet is registered with a DefaultRouter at the router root for `projects` (so the endpoints above are generated automatically). Check `projects/views.py` and `projects/serializers.py` for required fields and permissions.

## Example requests

- Obtain token:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

- Register user:

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"password123"}'
```

- Create checkout session (authenticated):

```bash
curl -X POST http://localhost:8000/api/accounts/create-checkout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"plan":"pro"}'
```

- Example to call a protected projects endpoint:

```bash
curl -X GET http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer <access_token>"
```

## Stripe-specific details (from code)

- The code uses Stripe Checkout in subscription mode and verifies webhooks with `stripe.Webhook.construct_event(...)`.
- The view maps a small set of plan names to Stripe price IDs (as defined in `accounts/views.py`):

```python
PRICE_MAPPING = {
    "free": "price_1SthW5RrDv86DUZ",
    "pro": "price_1StVkue5",
    "premium": "price_1SthXifmT60Lwd1l",
}
```

- The Checkout Session is created with:
  - `mode='subscription'`
  - `customer_email` set to `request.user.email`
  - `line_items` with the mapped price ID
  - `success_url` set to: `http://localhost:8000/api/accounts/success?session_id={CHECKOUT_SESSION_ID}`
  - `cancel_url` set to: `http://localhost:8000/api/accounts/cancel/`
  - `metadata` includes `user_id` so the webhook can associate the session with a local user

- Webhook behavior:
  - On `checkout.session.completed`, the webhook reads `session['metadata']['user_id']` and uses it to create/update a `Subscription` record:
    - sets `plan` to `'free'` in the current code (you may want to adjust to use the actual purchased plan)
    - sets `is_active` = True and `expires_at` = now + 30 days

## Webhook testing (local)

1. Run ngrok (or another tunneling tool) to forward a public HTTPS URL to your local server:

```bash
ngrok http 8000
```

2. Add a webhook endpoint in Stripe pointing to:
   `https://<ngrok-id>.ngrok.io/api/accounts/stripe/webhook/`

3. Copy the webhook signing secret from Stripe and set `STRIPE_WEBHOOK_SECRET` in your environment.

4. Trigger test events from the Stripe Dashboard and verify that your server processes them.

## Security & production notes

- Use Stripe live keys only in production.
- Always verify webhook signatures using `STRIPE_WEBHOOK_SECRET`.
- Use HTTPS for webhook and checkout endpoints in production.
- Store secrets in environment variables or a secrets manager.
- Improve webhook idempotency handling and use the Stripe event ID to avoid duplicate processing.
- Adjust the webhook logic to set the subscription `plan` to the true purchased plan (current code sets `'free'`).

## Running

1. Migrate and create superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

2. Run development server:

```bash
python manage.py runserver
```

3. Use the endpoints above to register, obtain tokens, create checkout sessions, and test webhooks.

## Project structure (high level)

- manage.py
- requirements.txt
- accounts/       — registration, checkout session creation, webhook handler
- projects/       — ProjectModel, serializers, viewset and URLs
- projectapi/     — Django project settings, URLs

## Tests

Run tests (if present):

```bash
python manage.py test
```

## Contributing & License

- Fork the repository and create a branch for your change
- Add tests for any new/changed behavior
- Open a pull request describing the change

Add a LICENSE file if you want to publish under a specific license (e.g., MIT).
