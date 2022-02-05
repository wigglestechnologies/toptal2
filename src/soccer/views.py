from django.http import HttpResponseBadRequest
import json

def error400(request, exception):
    response_data = {}
    response_data['message'] = "Bad request. Path doesn't exist!"
    return HttpResponseBadRequest(json.dumps(response_data), content_type="application/json")
