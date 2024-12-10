import sys
import threading
sys.path.append("..")
sys.path.append(".")
from spectral_explorer.run import SpectralRuntime
import dotenv
import os


#get our api key for open-ai

#create the runtime
runtime = SpectralRuntime(
    {
        'model': "llama-3.2-1b-instruct",
    }
)

runtime.run_backend_logic()