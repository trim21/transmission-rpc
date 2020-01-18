# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.


class TransmissionError(Exception):
    """
        This exception is raised when there has occurred an error related to
        communication with Transmission. It is a subclass of Exception.
    """
    def __init__(self, message='', original=None):
        Exception.__init__(self)
        self.message = message
        self.original = original

    def __str__(self):
        if self.original:
            original_name = type(self.original).__name__
            return '{} Original exception: {}, "{}"'.format(
                self.message, original_name, str(self.original)
            )
        else:
            return self.message


class TransmissionAuthError(TransmissionError):
    pass
