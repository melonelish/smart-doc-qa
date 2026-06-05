"""
Custom exception hierarchy for SmartDocQA.
Used by global exception handlers in main.py.
"""

from fastapi import HTTPException


class AppException(HTTPException):
    """Base application exception — maps to a specific HTTP status."""

    def __init__(self, status_code: int, message: str, detail: str = None):
        super().__init__(
            status_code=status_code,
            detail=detail or message,
        )
        self.message = message


class DocumentNotFoundError(AppException):
    """Raised when a requested document does not exist."""

    def __init__(self, doc_id: str):
        super().__init__(
            status_code=404,
            message=f"文档不存在: {doc_id}",
            detail=f"未找到 ID 为 {doc_id} 的文档",
        )


class DocumentNotReadyError(AppException):
    """Raised when trying to query an unprocessed document."""

    def __init__(self, doc_id: str):
        super().__init__(
            status_code=400,
            message=f"文档尚未处理: {doc_id}",
            detail=f"文档 {doc_id} 尚未完成处理，请先调用 /process 接口",
        )


class VectorStoreNotFoundError(AppException):
    """Raised when vector store cannot be loaded (missing or corrupt)."""

    def __init__(self, doc_id: str):
        super().__init__(
            status_code=404,
            message=f"向量库不存在: {doc_id}",
            detail=f"文档 {doc_id} 的向量库未找到或已损坏，请重新处理文档",
        )


class NoRelevantContentError(AppException):
    """Raised when no document chunks are relevant to the question."""

    def __init__(self):
        super().__init__(
            status_code=204,
            message="未找到相关内容",
            detail="文档中没有找到与问题相关的内容",
        )


class FileTypeNotAllowedError(AppException):
    """Raised when an uploaded file has an unsupported type."""

    def __init__(self, ext: str, allowed: str):
        super().__init__(
            status_code=400,
            message=f"不支持的文件类型: {ext}",
            detail=f"文件扩展名 {ext} 不在允许列表内: {allowed}",
        )


class FileTooLargeError(AppException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, size_mb: float, limit_mb: int):
        super().__init__(
            status_code=413,
            message=f"文件过大 ({size_mb:.1f}MB)，超过限制 ({limit_mb}MB)",
            detail=f"上传文件大小 {size_mb:.1f}MB 超过了 {limit_mb}MB 上限",
        )


class ProcessingError(AppException):
    """Raised when document processing fails."""

    def __init__(self, reason: str):
        super().__init__(
            status_code=500,
            message="文档处理失败",
            detail=reason,
        )


class QAError(AppException):
    """Raised when the Q&A pipeline encounters an error."""

    def __init__(self, reason: str):
        super().__init__(
            status_code=500,
            message="问答服务异常",
            detail=reason,
        )


class ConfigurationError(AppException):
    """Raised when a required external service is not configured."""

    def __init__(self, message: str):
        super().__init__(
            status_code=400,
            message=message,
            detail=message,
        )
