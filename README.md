# Backend Project

This is the backend service for the Backend project, built with FastAPI.

## Project Structure

The project follows a modular structure for better maintainability and scalability:

- **app/**: Main application directory.
    - **api/**: API route definitions and controllers.
    - **core/**: Core configurations (settings, security, constants).
    - **crud/**: CRUD (Create, Read, Update, Delete) logic for database interactions.
    - **db/**: Database connection and session management.
    - **models/**: Database models (ORM definitions).
    - **schemas/**: Pydantic schemas for data validation and serialization.
    - **services/**: Business logic layer.
    - **main.py**: Application entry point.
- **requirements.txt**: Project dependencies.

## Run the project

```bash
python -m uvicorn app.main:app --reload
```
