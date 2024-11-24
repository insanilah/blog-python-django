from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    # print("Response data:")
    
    if response is not None:
        custom_response = {
            'status': 'error',
            'message': 'Validation failed.',
            'errors': response.data
        }
        return Response(custom_response, status=response.status_code)
    
    return response
