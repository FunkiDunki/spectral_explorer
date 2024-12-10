import os
import pickle
import tkinter as tk
import threading
from devtools import pprint
from openai import OpenAI

import sys
sys.path.append(".")


from .configs import DEFAULT_RUNTIME_CONFIG, DEFAULT_FRONTEND_CONFIG
from .utils import (
    World,
    Player,
    generate_main_history,
    generate_cities,
    generate_regions,
    place_player_region,
    place_player_subregion,
    explore_subregion,
    help_player_move
)
from .gui import (
    TextAdventureGameGUI,
    SkimmedFrontend
)

class SpectralRuntime():
    def __init__(self, config: dict = {}, frontend_config: dict={}):
        '''
        Initialize the spectral explorer runtime
        Arguments: 
            config: Optional Configuration for the runtime.
            frontend_config: Optional Configuration for the frontend.
        '''
        #override the default config with any provided configuration (if any)
        self.config = {**DEFAULT_RUNTIME_CONFIG, **config}

        #create the client:
        self.client = OpenAI(base_url=self.config['url'], api_key=self.config['api-key'])
        self.model = self.config['model']


        #frontend connection:
        if self.config['frontend-active']:
            self.tk_root = tk.Tk()
            new_frontend_config = {**DEFAULT_FRONTEND_CONFIG, **frontend_config}
            
            self.frontend = TextAdventureGameGUI(self.tk_root, new_frontend_config)
        else:
            self.frontend= SkimmedFrontend()


        self.user_input = None
        self.input_received = threading.Event()

    def start_gui(self):
        '''
        Start the GUI in the main thread.
        '''
        if self.config['frontend-active']:
            self.tk_root.after(0, self.tk_root.mainloop)

    def run_backend_logic(self):
        '''
        Run the backend logic.
        '''
        self.run(
            story_prompt=(
                self.config['story-prompt']
            ),
            load_file=(self.config['output_dir']+'/'+self.config['save-name']),
            load_level=2,
            verbose=True
        )

    def stop_gui(self):
        '''
        Stop the GUI in the main thread.
        '''
        self.tk_root.quit()

    def get_input_from_frontend(self, prompt):
        ''' 
        Send a prompt to the frontend and wait for user input.
        Arguments:
            prompt: A prompt to send to frontend before user input.
        '''
        # Ensure a frontend instance is connected
        if not self.frontend:
            raise ValueError("Frontend is not connected.")

        # Clear the event to prepare for a fresh input wait
        self.input_received.clear()

        # Display the prompt message to the frontend
        self.frontend.display_message(prompt)

        # Set the callback to handle user input
        self.frontend.set_input_callback(self.handle_frontend_input)

        # Block execution until input is received and event is set
        self.input_received.wait()

        # Return the input provided by the user
        return self.user_input

    def wait_for_input(self):
        ''' 
        Non-blocking function to wait for input.
        '''
        if self.user_input is not None:
            self.input_received.set()  # Signal that input was received

    def handle_frontend_input(self, user_input):
        '''
        Handle input received from the frontend.
        Arguments: 
            user_input: A string representing user input.
        '''
        self.user_input = user_input
        self.input_received.set()
    
    def load_world(self, filename: str=None):
        '''
        Load the game world from a file.
        Arguments:
            filename: Path to the file containing saved world data.
        '''
        pass

    def run(self, story_prompt: str, verbose: bool, load_level: int, load_file: str):
        '''
        Execute the game world creation and exploration process.
        Arguments:
            story_prompt: Initial story description to generate the world.
            verbose: Determines whether detailed output is displayed.
            load_level: Level of saved data to load (0: basic, 1: regions, 2: full details).
            load_file: Filepath for loading or saving the world data.
        '''
        
        # Initialize a new World object with empty attributes
        world = World(
            history="",
            regions=[],
            all_nodes = {},
            player=Player()
        )

        # Check if loading from a save file
        if load_level >= 0 and os.path.exists(load_file):
            # Load the saved game world using pickle
            with open(load_file, 'rb') as file:
                world_save = pickle.load(file) # Deserialize the saved world state
            world_save: World
            world.history= world_save.history # Load the world's history
            world.next_id = world_save.next_id
        else:
            # No save file found, start from scratch
            self.frontend.display_message("no save found, starting from scratch.")
            world_save = None
            # Generate the main story history using the provided prompt
            world.history = generate_main_history(story_prompt=story_prompt, model=self.model, client=self.client)
            
            if verbose:
                #try to print that out:
                pprint(f"Story: {world.history}")

        # Load regions and nodes if specified by load_level
        if load_level >= 1 and world_save is not None:
            for key in world_save.regions:
                world.regions.append(key) # Add regions to the new world
                world.all_nodes[key] = world_save.all_nodes[key].model_copy() # Copy all nodes

                if load_level >= 2:
                    # Copy children nodes if load_level is 2
                    for child_key in world.all_nodes[key].children:
                        world.all_nodes[child_key] = world_save.all_nodes[child_key].model_copy()
                else:
                    # Reset children nodes for load_level 1
                    world.all_nodes[key].children = []

        else:
            # Generate regions if no save file or insufficient load_level
            self.frontend.display_message("Generating regions...")
            world = generate_regions(
                world=world,
                model=self.model,
                client=self.client,
                update_schema=self.config['update-schema']
            )
        
        # Save the world state if load_level >= 0
        if load_level >= 0:
            with open(load_file, 'wb') as file:
                pickle.dump(world, file)
            self.frontend.display_message(f"Saved world into file: {load_file}.")
        
        # Place player in the initial region
        world = place_player_region(world, self.frontend.display_message, self.get_input_from_frontend)

        # Generate cities in the world
        world = generate_cities(
            world=world,
            model=self.model,
            client=self.client,
            update_schema=self.config['update-schema']
        )

        # Place player in a subregion
        world = place_player_subregion(world, self.frontend.display_message, self.get_input_from_frontend)

        # Main game loop for exploration and movement
        while True:
            if load_level >= 0:
                #save the world
                with open(load_file, 'wb') as file:
                    pickle.dump(world, file)
                self.frontend.display_message(f"Saved world into file: {load_file}.")
            
            # Explore the current subregion
            world = explore_subregion(
                world=world,
                model=self.config['model'],
                client=self.client,
                print_output=self.frontend.display_message,
                get_input=self.get_input_from_frontend
            )

            # Help player move to a different subregion or region
            world = help_player_move(
                world=world,
                model=self.model,
                client=self.client,
                print_output=self.frontend.display_message,
                get_input=self.get_input_from_frontend,
                update_schema=self.config['update-schema']
            )