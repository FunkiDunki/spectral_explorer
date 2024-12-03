import sys
sys.path.append("..")
from spectral_explorer.run import SpectralRuntime

#create the runtime
runtime = SpectralRuntime()

#begin the run
runtime.run(
    story_prompt=(
        "write about the history of a magical world called akhel. "
        "Focus on important events that might impact the world, or the citizens of it."
    ),
    load_file="./saves/world_akhel.pkl",
    load_level=2,
    verbose=True
)