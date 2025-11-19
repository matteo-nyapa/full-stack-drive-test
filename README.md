# Mini Drive – Full Stack Developer Technical Test

A lightweight cloud‑drive style application built with **FastAPI**, **MongoDB**, **MinIO**, and **SvelteKit**.  
This project runs fully inside **Docker** using `docker compose`.

---

## 🚀 Features

### Backend (FastAPI)
- User registration & login with JWT authentication  
- File upload, download, rename, delete  
- Folder creation and nested folder structure  
- File metadata stored in MongoDB  
- Files stored in MinIO S3-compatible storage  
- CORS enabled for frontend communication

### Frontend (SvelteKit)
- Login & registration UI  
- File manager interface  
- Folder tree navigation  
- File uploads / downloads  
- Rename and delete actions  

---

## 📦 Technologies Used

| Layer | Stack |
|------|-------|
| Backend | FastAPI, Motor (MongoDB), MinIO client, JWT |
| Frontend | SvelteKit, TypeScript, TailwindCSS |
| Storage | MongoDB, MinIO (S3) |
| Infrastructure | Docker & Docker Compose |

---

## 🐳 Running the Project with Docker

Make sure you have **Docker** and **Docker Compose** installed.

### 1. Clone the repo
```bash
git clone https://github.com/matteo-nyapa/full-stack-drive-test.git
cd full-stack-drive-test
```

### 2. Create your `.env` file

Inside the `backend/` directory create a file named `.env`:

```
MONGO_URI=mongodb://mongo:27017
MONGO_DB=drive
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=drive
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```

### 3. Start all services
```bash
docker compose up --build
```

This will start:
- `backend` → FastAPI (port **8000**)  
- `frontend` → SvelteKit (port **5173**)  
- `mongo` → database  
- `minio` → S3 storage (port **9001**)  
- `minio-console` → MinIO Console UI (port **9005**)  

---

## 🌐 Accessing the App

| Service | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9005 (user: minioadmin / minioadmin) |

---

## 🔐 Authentication Workflow

1. Register a new user via the UI (`/auth/register`)
2. Log in to receive a JWT token
3. All file & folder APIs require Bearer Token authentication
4. The frontend stores the token and sends it automatically

---

## 📁 Folder & File Structure

```
full-stack-drive-test/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── models/
│   │   ├── auth_utils.py
│   │   └── main.py
│   ├── tests/   (unused)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── .svelte-kit/
│   └── Dockerfile
└── docker-compose.yml
```

---

## 🧹 Stopping Containers

```bash
docker compose down
```

---

## 📝 Notes

- Test suite exists but is not required or executed for this submission.
- Project intentionally keeps a simple architecture for readability.
- Backend & frontend automatically reload thanks to Docker volume mounts.

---

## ✅ Completed Optional Features

- ✔ User authentication (JWT)
- ✔ Persistent folders
- ✔ Nested folder support
- ✔ MinIO file storage
- ✔ Frontend UI improvements

---

## 📄 License

This project is for technical evaluation purposes only.
