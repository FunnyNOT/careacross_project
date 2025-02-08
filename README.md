# CareAcross Project

## 📌 Overview
The **CareAcross Project** is a Django-based application that fetches **Todo** data from an external API when the database is empty, saves them in PostgreSQL, and displays them in a UI. Users can view todos and update their **completed status**.

## 🎯 Target Audience
This project is an **assignment** and serves as a demonstration of working with external APIs, Django ORM, and Dockerized development.

---

## 🚀 Technology Stack
The project is built using:
- **Django** (Backend)
- **HTML, CSS, JavaScript** (Frontend UI)
- **PostgreSQL** (Database)
- **Docker** (Containerized development)

---

## 🛠️ Installation Instructions

The project uses **Docker Compose** and a **Makefile** for easy setup. To install and run the project locally:

### Prerequisites


#### All tests were done on **Ubuntu 24.04**. If you need any assistance please do let me know via email.

  1.  ```Docker```
  2.  ```Docker - Compose```
  3.  ```Python 3.11^```
  4.  ```Python 3 setuptools```
  5.  ```Make```  For easier access to commands using the Makefile in the root of the project
  6.  ```.env values``` Granted via email request


### 

2. **Clone the repository:**
   ```sh
   git clone https://github.com/FunnyNOT/careacross_project.git
   cd careacross_project
   ```

3. **Set up environment variables:**

   ##### Copy the example .env file:
    ```sh
    cp env.example .env
    ```

   ##### Update .env with your own values:
    ```sh
    SECRET_KEY=<django-secret-key>
    DEBUG=<django-debug>
    ALLOWED_HOSTS=<django-allowed-hosts>
    DATABASE_STRING=<django-database-string>
    TODO_API_URL=<todo-api-url>
    ```


3. **Build and run the project using Docker Compose:**

    ```sh
    make build
    make up
    ```
    ##### Run database migrations:
    ```sh
    make migrate
    ```



## 📌 Usage Instructions
Once the project is running:

View Todos → Access the UI to see all todos categorized here:
```http://localhost:8000/```

## All Todos
1. Completed Todos
2. Pending Todos
3. Update Todos → Change the completed status of any todo.

## 🧪 Running Tests
To run the test suite:

1. Ensure containers are running:

    ```sh
    make up
    ```

2. Run tests:

    ```sh
    make test
    ```

## ⚙️ Configuration & Environment Variables

### The following environment variables need to be set (stored in .env):
    
    SECRET_KEY	    # Django secret key
    DEBUG	        # Django debug mode (True/False)
    ALLOWED_HOSTS	# Allowed hosts for Django
    DATABASE_STRING	# PostgreSQL connection string
    TODO_API_URL	# External API URL for fetching todos

## 🔧 Makefile Commands
The project includes a Makefile for simplified development tasks:

### Command	Description:

| Commands              | Description |
| -----------           | ----------- |
| make build            | Build Docker images|
| make down	            | Stop and remove containers|
| make up               | Start the containers|
| make logs             | View application logs|
| make restart          | Restart the containers|
| make migrate          | Apply database migrations|
| make collectstatic    | Collect Django static files|
| make shell	        | Open a Bash shell inside the backend container|
| make dbshell          | Open a psql shell in the database container|
| make format           | Format code using black and isort|
| make lint             | Run ruff for linting|
| make format_lint      | Format and lint in one go|
| make test             | Run Django tests|



## 🚀 Deployment Instructions
This project is not deployed yet, but to deploy it, you would need:

1. A production-ready Dockerfile (different from the current development version).
2. A PostgreSQL database instance (e.g., AWS RDS, Azure PostgreSQL, or self-hosted).
3. A production-ready server (e.g., AWS, DigitalOcean, or self-hosted VPS).
4. A CI/CD pipeline for automated deployments.

## 📏 Code Style & Linting
The project follows PEP8 and uses:

- Black (Code formatting)
- Isort (Import sorting)
- Ruff (Linting)
- To apply formatting and linting:

    ```sh
    make format_lint
    ```

👨‍💻 Author & Contact
Project created by Leonidas Oikonomou.
📧 Email: leonidas.oikonomou17@gmail.com
🌍 GitHub: [FunnyNOT](https://github.com/FunnyNOT)