from typing import Any
from typing import Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class CommonResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any]


def server_response(
    status_code: int,
    data: Optional[Any] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    is_success = 200 <= status_code < 400
    resolved_message = message or ("OK" if is_success else "Error")
    payload = CommonResponse(
        success=is_success,
        message=resolved_message,
        data=data,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())
