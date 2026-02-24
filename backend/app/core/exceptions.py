from typing import Optional, Any


class CodeInsightException(Exception):
    """CodeInsight 基础异常类。

    所有自定义异常都应该继承自此类。
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 400,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """将异常转换为字典格式，用于 API 响应。

        Returns:
            dict: 异常信息字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ==================== 项目相关异常 ====================


class ProjectNotFoundError(CodeInsightException):
    """项目不存在异常。

    当请求的项目 ID 在数据库中不存在时抛出。
    """

    def __init__(self, project_id: str):
        super().__init__(
            message=f"项目不存在: {project_id}",
            code="PROJECT_NOT_FOUND",
            status_code=404,
            details={"project_id": project_id},
        )


class ProjectAlreadyExistsError(CodeInsightException):
    """项目已存在异常。

    当尝试创建已存在的项目时抛出。
    """

    def __init__(self, project_name: str):
        super().__init__(
            message=f"项目已存在: {project_name}",
            code="PROJECT_ALREADY_EXISTS",
            status_code=409,
            details={"project_name": project_name},
        )


class InvalidProjectSourceError(CodeInsightException):
    """无效的项目来源异常。

    当用户提供无效的项目来源类型时抛出。
    """

    def __init__(self, source_type: str, reason: str):
        super().__init__(
            message=f"无效的项目来源: {source_type}",
            code="INVALID_PROJECT_SOURCE",
            status_code=400,
            details={"source_type": source_type, "reason": reason},
        )


class ProjectIndexingError(CodeInsightException):
    """项目索引异常。

    当项目解析或索引过程失败时抛出。
    """

    def __init__(self, project_id: str, reason: str):
        super().__init__(
            message=f"项目索引失败: {reason}",
            code="PROJECT_INDEXING_ERROR",
            status_code=500,
            details={"project_id": project_id, "reason": reason},
        )


# ==================== 解析相关异常 ====================


class ParseError(CodeInsightException):
    """代码解析失败异常。

    当解析代码文件失败时抛出。
    """

    def __init__(self, file_path: str, reason: str, details: Optional[dict] = None):
        super().__init__(
            message=f"解析文件失败: {file_path}",
            code="PARSE_ERROR",
            status_code=400,
            details={"file_path": file_path, "reason": reason, **(details or {})},
        )


class UnsupportedLanguageError(CodeInsightException):
    """不支持的语言异常。

    当尝试解析不支持的语言时抛出。
    """

    def __init__(self, language: str, file_path: str):
        super().__init__(
            message=f"不支持的语言: {language}",
            code="UNSUPPORTED_LANGUAGE",
            status_code=400,
            details={"language": language, "file_path": file_path},
        )


class UnsupportedFileExtensionError(CodeInsightException):
    """不支持的文件扩展名异常。

    当尝试解析不支持扩展名的文件时抛出。
    """

    def __init__(self, extension: str, file_path: str):
        super().__init__(
            message=f"不支持的文件类型: {extension}",
            code="UNSUPPORTED_EXTENSION",
            status_code=400,
            details={"extension": extension, "file_path": file_path},
        )


# ==================== 索引相关异常 ====================


class IndexingError(CodeInsightException):
    """索引错误异常。

    当向量索引创建或更新失败时抛出。
    """

    def __init__(self, reason: str, project_id: Optional[str] = None):
        super().__init__(
            message=f"索引失败: {reason}",
            code="INDEXING_ERROR",
            status_code=500,
            details={"reason": reason, "project_id": project_id},
        )


class EmbeddingError(CodeInsightException):
    """Embedding 生成错误异常。

    当生成代码向量失败时抛出。
    """

    def __init__(self, reason: str):
        super().__init__(
            message=f"向量生成失败: {reason}",
            code="EMBEDDING_ERROR",
            status_code=500,
            details={"reason": reason},
        )


class VectorStoreError(CodeInsightException):
    """向量存储错误异常。

    当向量数据库操作失败时抛出。
    """

    def __init__(self, reason: str):
        super().__init__(
            message=f"向量存储错误: {reason}",
            code="VECTOR_STORE_ERROR",
            status_code=500,
            details={"reason": reason},
        )


# ==================== LLM 相关异常 ====================


class LLMError(CodeInsightException):
    """LLM 服务错误异常。

    当 LLM API 调用失败时抛出。
    """

    def __init__(self, reason: str, model: Optional[str] = None):
        super().__init__(
            message=f"LLM 服务错误: {reason}",
            code="LLM_ERROR",
            status_code=500,
            details={"reason": reason, "model": model},
        )


class LLMRateLimitError(CodeInsightException):
    """LLM API 限流异常。

    当超过 LLM API 调用频率限制时抛出。
    """

    def __init__(self, model: str, retry_after: Optional[int] = None):
        details = {"model": model}
        if retry_after is not None:
            details["retry_after"] = retry_after

        super().__init__(
            message=f"LLM API 调用频率超限",
            code="LLM_RATE_LIMIT",
            status_code=429,
            details=details,
        )


class LLMQuotaExceededError(CodeInsightException):
    """LLM 配额用尽异常。

    当 LLM API 配额用尽时抛出。
    """

    def __init__(self, model: str):
        super().__init__(
            message=f"LLM API 配额已用尽",
            code="LLM_QUOTA_EXCEEDED",
            status_code=429,
            details={"model": model},
        )


class LLMTimeoutError(CodeInsightException):
    """LLM 请求超时异常。

    当 LLM API 请求超时时抛出。
    """

    def __init__(self, model: str, timeout: int):
        super().__init__(
            message=f"LLM API 请求超时（{timeout}秒）",
            code="LLM_TIMEOUT",
            status_code=504,
            details={"model": model, "timeout": timeout},
        )


# ==================== 导入相关异常 ====================


class ImportError(CodeInsightException):
    """项目导入错误异常。

    当导入项目失败时抛出。
    """

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"项目导入失败: {reason}",
            code="IMPORT_ERROR",
            status_code=400,
            details={"url": url, "reason": reason},
        )


class CloneError(CodeInsightException):
    """Git 克隆错误异常。

    当 Git 仓库克隆失败时抛出。
    """

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Git 克隆失败: {reason}",
            code="CLONE_ERROR",
            status_code=400,
            details={"url": url, "reason": reason},
        )


class InvalidURLError(CodeInsightException):
    """无效 URL 异常。

    当提供的项目 URL 无效时抛出。
    """

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"无效的 URL: {url}",
            code="INVALID_URL",
            status_code=400,
            details={"url": url, "reason": reason},
        )


# ==================== 验证相关异常 ====================


class ValidationError(CodeInsightException):
    """验证错误异常。

    当输入数据验证失败时抛出。
    """

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"验证失败: {field} - {reason}",
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, "reason": reason},
        )


class MissingRequiredFieldError(CodeInsightException):
    """缺少必填字段异常。

    当请求中缺少必填字段时抛出。
    """

    def __init__(self, field_name: str):
        super().__init__(
            message=f"缺少必填字段: {field_name}",
            code="MISSING_REQUIRED_FIELD",
            status_code=400,
            details={"field_name": field_name},
        )


class InvalidFormatError(CodeInsightException):
    """无效格式异常。

    当请求数据格式不正确时抛出。
    """

    def __init__(self, field: str, expected_format: str):
        super().__init__(
            message=f"无效格式: {field} 应为 {expected_format}",
            code="INVALID_FORMAT",
            status_code=400,
            details={"field": field, "expected_format": expected_format},
        )


# ==================== 功能分析相关异常 ====================


class FeatureAnalysisError(CodeInsightException):
    """功能分析错误异常。

    当功能分析失败时抛出。
    """

    def __init__(self, reason: str):
        super().__init__(
            message=f"功能分析失败: {reason}",
            code="FEATURE_ANALYSIS_ERROR",
            status_code=500,
            details={"reason": reason},
        )


# ==================== 文档生成相关异常 ====================


class DocumentationGenerationError(CodeInsightException):
    """文档生成错误异常。

    当生成文档失败时抛出。
    """

    def __init__(self, reason: str):
        super().__init__(
            message=f"文档生成失败: {reason}",
            code="DOCUMENTATION_GENERATION_ERROR",
            status_code=500,
            details={"reason": reason},
        )


# ==================== 图表生成相关异常 ====================


class GraphGenerationError(CodeInsightException):
    """图表生成错误异常。

    当生成可视化图表失败时抛出。
    """

    def __init__(self, graph_type: str, reason: str):
        super().__init__(
            message=f"{graph_type} 图表生成失败: {reason}",
            code="GRAPH_GENERATION_ERROR",
            status_code=500,
            details={"graph_type": graph_type, "reason": reason},
        )
