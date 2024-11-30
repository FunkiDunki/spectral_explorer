from .configs import DEFAULT_RUNTIME_CONFIG

class SpectralRuntime():
    def __init__(self, config: dict = {}):
        '''
        Initialize the spectral explorer runtime

        Arguments:
            -config: Optional Configuration for the runtime
        '''
        #override the default config with any provided configuration
        self.config = {**DEFAULT_RUNTIME_CONFIG, **config}