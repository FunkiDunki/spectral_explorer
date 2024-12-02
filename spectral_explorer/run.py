from .configs import DEFAULT_RUNTIME_CONFIG
import os
import pickle
from devtools import pprint

class SpectralRuntime():
    def __init__(self, config: dict = {}):
        '''
        Initialize the spectral explorer runtime

        Arguments:
            -config: Optional Configuration for the runtime
        '''
        #override the default config with any provided configuration
        self.config = {**DEFAULT_RUNTIME_CONFIG, **config}
    
    def load_world(self, filename: str=None):
        pass

    def run(story_prompt: str, verbose: bool, load_level: int, load_file: str):
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
        else:
            print("no save found, starting from scratch.")
            world_save = None
            world.history = generate_main_history(story_prompt)
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
            print("Generating regions...")
            world = generate_regions(world)
        
        if load_level >= 0:
            #save the world
            with open(load_file, 'wb') as file:
                pickle.dump(world, file)
            print(f"Saved world into file: {load_file}.")
        
        world = place_player_region(world)

        world = generate_cities(world)

        world = place_player_subregion(world)

        while True:
            if load_level >= 0:
                #save the world
                with open(load_file, 'wb') as file:
                    pickle.dump(world, file)
                print(f"Saved world into file: {load_file}.")
            world = explore_subregion(world)
            world = help_player_move(world)