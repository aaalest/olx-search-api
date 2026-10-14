from init_app import initialize_db
import uvicorn

if __name__ == "__main__":
    initialize_db()
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)