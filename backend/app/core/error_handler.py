import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import CodeInsightException
from app.core.config import settings

logger = logging.getLogger(__name__)


async def codeinsight_exception_handler(
    request: Request, exc: CodeInsightException
):
    """处理自定义 CodeInsight 异常。

    Args:
        request: FastAPI 请求对象
        exc: CodeInsightException 异常实例

    Returns:
        JSONResponse: JSON 格式的错误响应
    """
    # 记录错误日志
    logger.error(
        f"CodeInsightException: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details if settings.DEBUG or exc.status_code < 500 else {},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常。

    Args:
        request: FastAPI 请求对象
        exc: Starlette HTTP 异常实例

    Returns:
        JSONResponse: JSON 格式的错误响应
    """
    status_code = exc.status_code
    detail = getattr(exc, "detail", str(exc))

    # 记录警告日志
    logger.warning(
        f"HTTP Exception: {status_code} - {detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "code": f"HTTP_{status_code}",
            "message": detail if isinstance(detail, str) else "HTTP Error",
            "details": {},
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """处理请求验证异常。

    Args:
        request: FastAPI 请求对象
        exc: Pydantic 验证异常实例

    Returns:
        JSONResponse: JSON 格式的错误响应
    """
    # 提取验证错误详情
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    # 记录警告日志
    logger.warning(
        f"Validation Error: {len(errors)} field(s)",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": "VALIDATION_ERROR",
            "message": "请求数据验证失败",
            "details": {"errors": errors},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """处理通用异常（未捕获的异常）。

    Args:
        request: FastAPI 请求对象
        exc: 未捕获的异常实例

    Returns:
        JSONResponse: JSON 格式的错误响应
    """
    # 记录完整堆栈
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
            "exception_type": type(exc).__name__,
        },
    )

    # 在生产环境中不返回详细错误信息
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "details": (
                {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                if settings.DEBUG
                else {}
            ),
        },
    )
