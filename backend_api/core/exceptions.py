from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and 'code' in response.data:
        # Si "code" est une liste avec un seul élément, extraire cet élément
        if isinstance(response.data['code'], list) and len(response.data['code']) == 1:
            response.data['code'] = response.data['code'][0]
        # Convertir en entier si possible
        if isinstance(response.data['code'], (str, int)) and str(response.data['code']).isdigit():
            response.data['code'] = int(response.data['code'])
    return response
