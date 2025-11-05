from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class ResponseContext:
    def __init__(self):
        self._attributes = {}
        self.data = None
        self.status_code = status.HTTP_200_OK
        self.message = "success"

    def update(self, success: bool, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        if not success:
            self.data = None

    def __setattr__(self, name, value):
        if name in ["data", "status_code", "message", "_attributes"]:
            super().__setattr__(name, value)
        else:
            self._attributes[name] = value

    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def build(self):
        response = {
            "status_code": self.status_code,
            "message": self.message,
            "data": jsonable_encoder(self.data)
        }
        response.update(self._attributes)
        return JSONResponse(response, status_code=self.status_code)
