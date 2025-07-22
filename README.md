# hexagon-api

## 🚀 Local Development Setup

### 1. Create and activate virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application locally

```bash
uvicorn main:app --reload --app-dir app
```

---

## 🐳 Running with Docker

### 1. Build the Docker image

```bash
docker build -t hexagon-api .
```

### 2. Run the Docker container

```bash
docker run -p 8000:8000 hexagon-api
```

You can then access the app at [http://localhost:8000](http://localhost:8000)

---

## 🛠 Using Makefile Commands

The Makefile includes helpful shortcuts for common tasks.

### Available targets:

- **`make install`**: Install dependencies from `requirements.txt`
- **`make run`**: Run the app using Uvicorn
- **`make docker-build`**: Build the Docker image
- **`make docker-run`**: Run the Docker container

### Example usage:

```bash
make install
make run
```

---
