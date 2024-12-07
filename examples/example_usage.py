import sys
import threading
sys.path.append("..")
from spectral_explorer.run import SpectralRuntime

#create the runtime
runtime = SpectralRuntime({'model': "llama-3.2-1b-instruct"})

def run_backend_logic():
    """Run the backend logic in a separate thread."""
    threading.Thread(target=runtime.run_backend_logic, daemon=True).start()

runtime.start_gui()

#begin the run
runtime.tk_root.after(100, run_backend_logic)  # Run backend logic after 100ms (adjust as needed)

# Start the Tkinter main loop (this keeps the GUI responsive)
runtime.tk_root.mainloop()