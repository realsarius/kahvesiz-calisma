from flask import jsonify


def success_response(data=None, status=200, meta=None):
    return jsonify({"data": data, "error": None, "meta": meta or {}}), status


def error_response(message, status=400, code=None, details=None, meta=None):
    error = {"message": message}
    if code:
        error["code"] = code
    if details is not None:
        error["details"] = details
    return jsonify({"data": None, "error": error, "meta": meta or {}}), status

