class HTTPRequestError(Exception):
    """Basic exception."""


class AnotherEndpointException(Exception):
    """Some Endpoint errors."""


class SendMessageException(Exception):
    """Can't send the message."""
