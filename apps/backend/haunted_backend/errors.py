class GameError(Exception):
    def __init__(
        self,
        code,
        status=409,
        message="That action is not available.",
        revision=None,
        retryable=False,
    ):
        super().__init__(message)
        self.code, self.status, self.message = code, status, message
        self.revision, self.retryable = revision, retryable

    def response(self, request_id=None):
        return {
            "contract_version": "1.0.0",
            "error": {
                "code": self.code,
                "message": self.message,
                "request_id": request_id,
                "current_revision": self.revision,
                "retryable": self.retryable,
            },
        }
