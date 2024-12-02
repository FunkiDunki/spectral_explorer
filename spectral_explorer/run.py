import os
import pickle
from devtools import pprint
from openai import OpenAI


from .configs import DEFAULT_RUNTIME_CONFIG
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


class SpectralRuntime():
    def __init__(self, config: dict = {}):
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
            print("no save found, starting from scratch.")
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
            print("Generating regions...")
            world = generate_regions(
                world=world,
                model=self.model,
                client=self.client
            )
        
        if load_level >= 0:
            #save the world
            with open(load_file, 'wb') as file:
                pickle.dump(world, file)
            print(f"Saved world into file: {load_file}.")
        
        world = place_player_region(world)

        world = generate_cities(
            world=world,
            model=self.model,
            client=self.client
        )

        world = place_player_subregion(world)

        while True:
            if load_level >= 0:
                #save the world
                with open(load_file, 'wb') as file:
                    pickle.dump(world, file)
                print(f"Saved world into file: {load_file}.")
            world = explore_subregion(
                world=world,
                model=self.config['model'],
                client=self.client
            )
            world = help_player_move(
                world=world,
                model=self.model,
                client=self.client
            )