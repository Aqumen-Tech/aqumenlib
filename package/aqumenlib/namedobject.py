# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from abc import ABC, abstractmethod


class NamedObject(ABC):
    """
    Some objects must have names, e.g. instruments must provide
    names so that market risk results can be properly annotated.
    """

    @abstractmethod
    def get_name(self):
        """
        Identifier (human readable name) of an object
        """
        pass
