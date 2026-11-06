import sys
import uvicorn

from config import settings


if __name__ == "__main__":
    is_debugging = "pydevd" in sys.modules
    uvicorn.run("api:app", host="127.0.0.1", port=settings.api_port, reload=not is_debugging)
