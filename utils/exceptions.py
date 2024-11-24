from rest_framework.views import exception_handler
from utils.response import api_response
from rest_framework.exceptions import ValidationError
import logging

# Buat logger untuk mencatat error
logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler untuk mengatur format respons API secara konsisten.
    """
    # Dapatkan respons default dari DRF
    response = exception_handler(exc, context)
    logger.error("Unhandled exception", exc_info=exc)  # Log error untuk debugging
    
    if response is not None:
        return api_response(
            code=response.status_code,
            message=_get_message_from_status(response.status_code),
            data=[],
            error=response.data,
            status=response.status_code
        )
        
    # Untuk error server 500 atau exception lain yang tidak ditangani
    return api_response(
        code=500,
        message="Internal Server Error",
        data=[],
        error=str(exc),  # Menampilkan pesan error mentah (opsional)
        status=500
    )

def _get_message_from_status(status_code):
    """
    Mengembalikan pesan berdasarkan status kode.
    """
    messages = {
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        400: "Bad Request",
        500: "Internal Server Error"
    }
    return messages.get(status_code, "Error")
