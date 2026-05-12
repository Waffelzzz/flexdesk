from typing import Any

from fastapi import Request


def query_aware_key_builder(
        func,
        namespace: str,
        request: Request,
        *args: Any,
        **kwargs: Any,
) -> str:
    path = request.url.path
    query_params = request.url.query

    if query_params:
        key = f"{namespace}:{path}?{query_params}"
    else:
        key = f"{namespace}:{path}"
    return key
