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
            -config: Optional Configuration for the runtime
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
        #Start the GUI in the main thread.
        if self.config['frontend-active']:
            self.tk_root.after(0, self.tk_root.mainloop)

    def run_backend_logic(self):
        """Run the backend logic."""
        self.run(
            story_prompt=(
                "write about the history of a magical world called akhel. "
                "Focus on important events that might impact the world, or the citizens of it."
            ),
            load_file="./saves/world_akhel.pkl",
            load_level=2,
            verbose=True
        )

    def stop_gui(self):
        self.tk_root.quit()

    def get_input_from_frontend(self, prompt):
        #Send a prompt to the frontend and wait for user input.
        if not self.frontend:
            raise ValueError("Frontend is not connected.")
        self.input_received.clear()
        self.frontend.display_message(prompt)
        self.frontend.set_input_callback(self.handle_frontend_input)
        self.input_received.wait()
        return self.user_input

    def wait_for_input(self):
        """Non-blocking function to wait for input."""
        if self.user_input is not None:
            self.input_received.set()  # Signal that input was received

    def handle_frontend_input(self, user_input):
        #Handle input received from the frontend.
        self.user_input = user_input
        self.input_received.set()
    
    def load_world(self, filename: str=None):
        pass

    def run(self, story_prompt: str, verbose: bool, load_level: int, load_file: str):
        world = World(
            history="",
            regions=[],
            all_nodes = {},
            player=Player()
        )

        #check for load file
        if load_level >= 0 and os.path.exists(load_file):
            #load from file
            with open(load_file, 'rb') as file:
                world_save = pickle.load(file)
            world_save: World
            world.history= world_save.history
            world.next_id = world_save.next_id
        else:
            self.frontend.display_message("no save found, starting from scratch.")
            world_save = None
            world.history = generate_main_history(story_prompt=story_prompt, model=self.model, client=self.client)
            if verbose:
                #lets try to print that out:
                pprint(f"Story: {world.history}")


        if load_level >= 1 and world_save is not None:
            for key in world_save.regions:
                world.regions.append(key)
                world.all_nodes[key] = world_save.all_nodes[key].model_copy()
                if load_level >= 2:
                    for child_key in world.all_nodes[key].children:
                        world.all_nodes[child_key] = world_save.all_nodes[child_key].model_copy()
                else:
                    world.all_nodes[key].children = []

        else:
            self.frontend.display_message("Generating regions...")
            world = generate_regions(
                world=world,
                model=self.model,
                client=self.client
            )
        
        if load_level >= 0:
            #save the world
            with open(load_file, 'wb') as file:
                pickle.dump(world, file)
            self.frontend.display_message(f"Saved world into file: {load_file}.")
        
        world = place_player_region(world, self.frontend.display_message, self.get_input_from_frontend)

        world = generate_cities(
            world=world,
            model=self.model,
            client=self.client
        )

        world = place_player_subregion(world, self.frontend.display_message, self.get_input_from_frontend)

        while True:
            if load_level >= 0:
                #save the world
                with open(load_file, 'wb') as file:
                    pickle.dump(world, file)
                self.frontend.display_message(f"Saved world into file: {load_file}.")
            world = explore_subregion(
                world=world,
                model=self.config['model'],
                client=self.client,
                print_output=self.frontend.display_message,
                get_input=self.get_input_from_frontend
            )
            world = help_player_move(
                world=world,
                model=self.model,
                client=self.client,
                print_output=self.frontend.display_message,
                get_input=self.get_input_from_frontend
            )