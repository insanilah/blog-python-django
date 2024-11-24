from rest_framework.response import Response

def api_response(code=200, message="success", data=None, error="", status=None):
    """
    Helper untuk membuat struktur respons API konsisten.
    Args:
        code (int): Kode status respons (200, 400, dll).
        message (str): Pesan sukses atau error.
        data (dict|list): Data yang akan dikirimkan ke klien.
        error (str): Pesan error (kosong jika tidak ada error).

    Returns:
        Response: Objek Response yang sesuai dengan struktur API.
    """
    if data is None:
        data = []
    
    # Gunakan status HTTP yang disesuaikan, jika tidak diberikan gunakan 'code'
    if status is None:
        status = code
        
    return Response({
        "code": code,
        "message": message,
        "data": data,
        "error": error
    }, status=status)
