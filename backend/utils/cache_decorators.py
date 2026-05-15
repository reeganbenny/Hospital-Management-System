"""Cache decorators for API responses and data helpers."""
from functools import wraps
from flask import current_app


def cached(key_prefix, timeout=600):
    """
    Decorator that caches the return value of the function under key_prefix.
    Use from within a Flask request context (current_app.cache must be available).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            c = getattr(current_app, "cache", None)
            key = key_prefix if isinstance(key_prefix, str) else key_prefix()
            if c:
                data = c.get(key)
                if data is not None:
                    return data
            data = fn(*args, **kwargs)
            if c:
                c.set(key, data, timeout=timeout)
            return data
        return wrapper
    return decorator
