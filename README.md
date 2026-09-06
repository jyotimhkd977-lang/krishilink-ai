# KrishiLink AI

KrishiLink AI is a frontend prototype for connecting farmers with buyers and logistics support through a simple agricultural marketplace experience.

## Features

- Farmer and consumer workflows
- Product selling wizard
- AI assistant interface
- Buyer-seller negotiation flow
- Logistics map view
- Responsive dashboard and authentication screens

## Run Locally

The frontend is a static web application and does not require a build step. The backend API runs separately from `backend/`.

1. Clone the repository.
2. Start the backend in a separate terminal:

	```bash
	cd backend
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	copy .env.example .env
	uvicorn app.main:app --reload
	```

3. Open `index.html` in a browser, or serve the folder with a local web server.

For example, with Python:

```bash
python -m http.server 8000
```

Then visit `http://localhost:5173`. The frontend checks the backend at `http://localhost:8000/api/v1/health` on startup and continues using demo data if the API is unavailable.

## Project Structure

```text
assets/    Images and other static assets
backend/   FastAPI backend service
css/       Stylesheets and design system files
js/        Application modules, API client, and feature logic
index.html Main application entry point
```
