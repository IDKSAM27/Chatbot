from flask import jsonify

from ....app import VERSION
from ...api import v1_router

__all__ = ("read_root",)


@v1_router.get("/")
def read_root():
    data = {"message": "Language Agnostic Chatbot", "status": "OK", "version": VERSION}
    return jsonify(data)
