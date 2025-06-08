# Django REST API

A modern Django REST API project with JWT authentication, Clerk integration, Dockerized deployment, and Nginx reverse proxy.

---

## Features

- Custom user model with email login
- JWT authentication (SimpleJWT)
- Clerk.com integration (webhooks, authentication)
- User profile, email, and phone management
- Admin interface (restricted to local network)
- OpenAPI/Swagger docs (restricted to local network)
- Dockerized with Gunicorn and Nginx
- Static/media file handling
- CORS and CSRF protection

---

## Project Structure

```
.
├── manage.py
├── docker-compose.yml
├── dockerfile
├── nginx.conf
├── requirements.txt
├── .env
├── srv/            # Django project settings, wsgi/asgi, urls
├── restAPI/        # Main API app (users, webhooks, auth, etc.)
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils/
│   └── ...
├── jobb/           # Example app (jobs, materials, etc.)
├── static/         # Collected static files (served by Nginx)
├── media/          # Uploaded media files (served by Nginx)
└── ...
```

---

## Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```
SECRET_KEY=your-django-secret
DB_NAME=yourdbname
DB_USER=yourdbuser
DB_PASSWORD=yourdbpassword
DB_HOST=yourdbhost
DB_PORT=3306
CLERK_URL=https://api.clerk.com
CLERK_SECRET_KEY=your-clerk-secret
CLERK_WEBHOOK_KEY=your-clerk-webhook-secret
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your-email-password
```

### 3. Build and Run with Docker

```sh
docker-compose up --build
```

- Django runs in the `restapi_django` container (Gunicorn, port 8000)
- Nginx runs in the `restapi_nginx` container (port 8080)
- Static and media files are mounted as volumes

### 4. Collect Static Files

If needed, run:

```sh
docker-compose run --rm django python manage.py collectstatic --noinput
```

---

## Usage

- **API root:** [http://localhost:8080/](http://localhost:8080/)
- **Admin:** [http://localhost:8080/admin/](http://localhost:8080/admin/) (local network only)
- **Swagger/OpenAPI:** [http://localhost:8080/schema/swagger-ui/](http://localhost:8080/schema/swagger-ui/) (local network only)
- **Clerk Webhook:** `/clerk/webhook/` (public, for Clerk events)

---

## Clerk Integration

- Users created in Clerk are synced to Django via webhook.
- JWT authentication via Clerk is supported.
- Webhook endpoint: `/clerk/webhook/` (see `restAPI/views.py`)

---

## Development

- Run locally with SQLite and Django dev server:
  ```sh
  python manage.py migrate
  python manage.py runserver
  ```
- For production, use Docker and configure your `.env` for MySQL.

---

## Security Notes

- Admin and schema docs are restricted to your local network via Nginx and custom middleware.
- CORS and CSRF settings are configured for secure cross-origin requests.
- Never commit your `.env` file or secrets to version control.

---

## License

MIT License

---

## Credits

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Clerk.com](https://clerk.com/)
- [Gunicorn](https://gunicorn.org/)
- [Nginx](https://nginx.org/)