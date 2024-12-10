import sys
import threading
sys.path.append("..")
sys.path.append(".")
from spectral_explorer.run import SpectralRuntime
import os



current_dir = os.path.dirname(os.path.abspath(__file__))
relative_path_to_image = "images/background.png"
background_image_path = os.path.join(current_dir, relative_path_to_image)

#create the runtime
runtime = SpectralRuntime(
    {
        'model': "llama-3.2-1b-instruct",
        "frontend-active": True,
        'url': 'http://localhost:1234/v1/',
    },
    frontend_config={
        'image-location': background_image_path,
        'show-image': True
    }
)

def run_backend_logic():
    """Run the backend logic in a separate thread."""
    threading.Thread(target=runtime.run_backend_logic, daemon=True).start()

runtime.start_gui()

#begin the run
runtime.tk_root.after(100, run_backend_logic)  # Run backend logic after 100ms (adjust as needed)

# Start the Tkinter main loop (this keeps the GUI responsive)
runtime.tk_root.mainloop()