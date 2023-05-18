class NotFoundException(Exception):
    def __init__(self, message, *args: object) -> None:
        self.message = message
