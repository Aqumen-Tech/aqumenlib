class AqumenException(Exception):
    """
    Basic exception class for Aqumen SDK.
    """

    def __init__(self, message="Exception in Aqumen SDK:"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"AqumenException: {self.message}"
