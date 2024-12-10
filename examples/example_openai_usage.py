import sys
sys.path.append("..")
sys.path.append(".")
from spectral_explorer.run import SpectralRuntime
import dotenv
import os


#get our api key for open-ai
dotenv.load_dotenv()

#create the runtime, to connect with openai
runtime = SpectralRuntime(
    {
        'model': 'gpt-4o-mini',
        'api-key': os.getenv("OPENAI_KEY")
    }
)

runtime.run_backend_logic()