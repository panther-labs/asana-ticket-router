class AirplaneTask:

    def __init__(self, is_dry_run: bool = False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        self.is_dry_run = is_dry_run

    def run(self, params: dict) -> any:
        """
        Main method of an Airplane task. Must be implemented in the concrete class
        :param params: Airplane parameters
        :return: Any value or None
        """
        raise NotImplementedError("The method must be implemented in the concrete class.")
