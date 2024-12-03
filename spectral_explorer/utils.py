from openai import OpenAI
from typing import List, Type, Dict
from pydantic import BaseModel, Field

def call_llm_unstructured(client: OpenAI, model: str, messages: List, temperature=0.8) -> str:
    '''
    Make api call to llm, for basic string
    '''

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=False
    ).choices[0].message.content

    return response

def update_schema(input_model: Type[BaseModel]) -> Dict[str, any]:
    #new update to lmstudio has stricter reqs for structured_output:
    tmp = input_model.model_json_schema()

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "test_schema",
            "strict": True,
            "schema": tmp
        }
    }

def call_llm_structured(client: OpenAI, model: str, messages: List, model_format: Type[BaseModel], temperature=0.8):
    '''
    Make api call to create an object with specified format, as a response from llm.
    '''

    #first get the schema for the model:
    schema = update_schema(model_format)

    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=schema,
        temperature=temperature,
    ).choices[0].message.content

    return model_format.model_validate_json(response)


# -------- Class Defnitions ---------

#      -----classes for generation:
#generating the original story can be unstructured.

#classes for generating the layer-1 regions
class SingleRegionResponse(BaseModel):
    name: str
    description: str
    derived_history: str
    current_dynamics: str
    
class RegionGenerateResponse(BaseModel):
    regions: List[SingleRegionResponse]

#classes for generating the layer-2 regions
class SingleSubRegionResponse(BaseModel):
    name: str
    description: str
    derived_history: str
    current_dynamics: str
    
class SubRegionGenerateResponse(BaseModel):
    subregions: List[SingleSubRegionResponse]

#     -----classes for actually storing the data

class Node(BaseModel):
    node_id: int
    node_name: str
    node_description: str
    derived_history: str
    current_dynamics: str
    outgoing_edges: List[int]
    children: List[int]

class Player(BaseModel):
    region_id: int = Field(default=-1)
    subregion_id: int = Field(default=-1)

class World(BaseModel):
    history: str
    regions: List[int]
    all_nodes: Dict[int, Node]
    player: Player
    next_id: int = Field(default=0)

# -------- Helper Funcs -------------


def generate_main_history(story_prompt: str, model: str, client: OpenAI) -> str:
    messages = [
        {"role": "system", "content": "You are a storyteller, describing the history of a world based on the user's prompt."},
        {"role": "user", "content": story_prompt},
    ]

    return call_llm_unstructured(client=client, model=model, messages=messages) 

def generate_regions(world: World, model:str, client:OpenAI) -> World:

    prompt = (
        "For the following world, describe 2-6 overall regions that exist. "
        "For each location, give a name and a physical description of key features of the location that might hint at the rich history. "
        "Also, describe a derived history, which contains a summary of events from the world history that influenced the region. "
        "Include also any relevant descriptions of current-day life in the region. "
    )
    messages = [
        {"role": "system", "content": "You are a designer of fantastic world, describing a world as the user desires."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": f"{world.history}"}
    ]

    result: RegionGenerateResponse = call_llm_structured(
        client=client,
        model=model, 
        messages=messages,
        model_format=RegionGenerateResponse
        ) 

    for region in result.regions:
        world.regions.append(world.next_id)
        world.all_nodes[world.next_id] = \
            Node(
                node_id=world.next_id,
                node_name=region.name,
                node_description=region.description,
                derived_history=region.derived_history,
                current_dynamics=region.current_dynamics,
                outgoing_edges=[],
                children=[]
            )
        world.next_id += 1
    
    return world

def generate_cities(world: World, model:str, client:OpenAI) -> World:
    '''
    Assuming the player has just entered a new region, generate the cities for that region (if they don't exist)
    '''

    if len(world.all_nodes[world.player.region_id].children) > 0:
        #the region has already been generated
        return world
    
    #now actually generate the cities
    prompt = (
        f"based on the history of the world and the descriptions of the main regions, list 2-5 sub-locations that might exist within the region of {world.all_nodes[world.player.region_id].node_name}. "
        "For each location, give a name and a physical description of key features of the location that might hint at the rich history of the region it is in. "
        "Also, describe a derived history, which contains a summary of any relevant events from the history of the region it is in. "
        "Include also any relevant descriptions of current-day life in the subregion. "
        "Don't generate a subregion named after the region it is in. "
    )
    info = get_relevant_information(world, exclusions=["history"])
    messages = [
        {"role": "system", "content": "You are a designer of fantastic world, expanding on how the regions and subregions connect to the world's story."},
        {"role": "user", "content": prompt},
        *info,
    ]

    result: SubRegionGenerateResponse = call_llm_structured(client, model, messages, SubRegionGenerateResponse) 

    for city in result.subregions:
        world.all_nodes[world.player.region_id].children.append(world.next_id)
        world.all_nodes[world.next_id] = \
            Node(
                node_id=world.next_id,
                node_name=city.name,
                node_description=city.description,
                derived_history=city.derived_history,
                current_dynamics=city.current_dynamics,
                outgoing_edges=[],
                children=[]
            )
        world.next_id += 1
    
    return world

def place_player_region(world: World) -> World:
    '''place the player into a region of their choosing to explore'''
    print(f"In this world, there are {len(world.regions)} main regions:")
    for i, region in enumerate(world.regions):
        print(f"\t({i+1}). {world.all_nodes[region].node_name}")
    
    choice = input("Pick the number of a region to explore!: ")
    while not (choice.isnumeric() and int(choice) >= 1 and int(choice) <= len(world.regions)):
        print("Whoops, that wasn't a valid choice!")
        choice = input("Pick the number of a region to explore!: ")
    
    choice = int(choice) - 1
    print(f"Okay! Let's explore {world.all_nodes[world.regions[choice]].node_name}!")

    world.player.region_id = world.regions[choice]

    return world

def get_relevant_information(world: World, exclusions: List[str] = []) -> List[dict]:
    '''based on the current state and location of player, get the relevant information for the model.'''

    result = []
    if "history" not in exclusions:
        result.append(
            {"role": "user", "content": f"Here is the full history of the world: {world.history}"}
        )

    if world.player.region_id != -1:

        #add info of the regions in the world
        regions_info = [
            {
                "name": world.all_nodes[region].node_name,
                "description": world.all_nodes[region].node_description,
                "connection_to_history": world.all_nodes[region].derived_history,
                "current_dynamics": world.all_nodes[region].current_dynamics
            }
            for region in world.regions
        ]
        result.append(
            {"role":"user", "content":f"There are a few main regions of the world: {regions_info}"})

        result.append(
            {"role":"user", "content":f"The player is in the main region of {world.all_nodes[world.player.region_id].node_name}"}
        )

        if world.player.subregion_id != -1:
            #add info of the subregions for the player's region
            subregions_info = [
                {
                    "name": world.all_nodes[region].node_name,
                    "description": world.all_nodes[region].node_description,
                    "connection_to_history_of_region": world.all_nodes[region].derived_history,
                    "current_dynamics": world.all_nodes[region].current_dynamics
                }
                for region in world.all_nodes[world.player.region_id].children
            ]
            result.append(
                {"role":"user", "content":f"Here are all generated subregions for this region so far: {subregions_info}"})
            result.append(
                {"role": "user", "content": f"The player is in the subregion called {world.all_nodes[world.player.subregion_id].node_name}"}
            )

    return result

def place_player_subregion(world: World) -> World:
    '''place the player into a subregion of their choosing to explore'''
    #find the player's region:
    
    region = world.all_nodes[world.player.region_id]

    print(f"In this region, there are {len(region.children)} subregions:")
    for i, subregion in enumerate(region.children):
        print(f"\t({i+1}). {world.all_nodes[subregion].node_name}")
    
    choice = input("Pick the number of a subregion to explore!: ")
    while not (choice.isnumeric() and int(choice) >= 1 and int(choice) <= len(region.children)):
        print("Whoops, that wasn't a valid choice!")
        choice = input("Pick the number of a subregion to explore!: ")
    
    choice = int(choice) -1

    print(f"Okay! Let's explore {world.all_nodes[region.children[choice]].node_name}!")

    world.player.subregion_id = region.children[choice]

    return world

def explore_subregion(world: World, model:str, client:OpenAI) -> World:
    '''explore a subregion (looping behavior). Return when the player wants to move'''

    subregion = world.all_nodes[
        world.player.subregion_id
    ]

    relevant_info = get_relevant_information(world, exclusions=["history"])

    #describe the region
    intro_prompt = (
        "The player is a wandering traveler, trying to learn about various regions of the world. "
        f"The player has entered the {subregion.node_name}. Describe the subregion as if the player is just entering the subregion. "
        "Don't describe the full history of the region. Instead, focus on "
        "Truly paint the scene vividly, including all that the player might see as they enter the region. "
    )

    messages = [
        {"role": "system", "content": "You are a storyteller, helping the player to explore the given world and discover its history."},
        {"role": "system", "content": "As the Dungeon Master, provide vivid, immersive descriptions of the world and its events. Avoid explicitly prompting the player with ‘What would you like to do next?’ or listing possible actions. "},
        *relevant_info,
        {"role": "user", "content": intro_prompt}
    ]
    print(('* ' * 10) + f"{world.all_nodes[world.player.subregion_id].node_name}" + (' *' * 10))

    choice = ""
    while choice.lower() != "move":
        result = call_llm_unstructured(client=client, model=model, messages=messages)
        print(result)
        messages.append(
            {"role": "assistant", "content": result}
        )
        choice = input("\nHow do you explore? 'move' to move to another region.\n>>> ")
        messages.append(
            {"role": "user", "content": f"The player said: {choice}"}
        )

    print(('* ' * 10) + f"left {world.all_nodes[world.player.subregion_id].node_name}" + (' *' * 10))
    return world

def help_player_move(world: World, model:str, client:OpenAI) -> World:
    '''the player wants to move. find out where, and move them!'''

    selection = None
    while selection is None:
        choice = input(f"Would you like to move to another subregion in {world.all_nodes[world.player.region_id].node_name}, or would you like to change regions?\n('region' or 'subregion') >>> ")
        choice = choice.lower()
        if choice == 'region':
            selection = 'region'
        elif choice == 'subregion':
            selection = 'subregion'
        else:
            print("Sorry, that's not a valid choice! ")
    
    if selection == 'subregion':
        world = place_player_subregion(world)
    elif selection == 'region':
        world = place_player_region(world)
        world = generate_cities(world, model, client)
        world = place_player_subregion(world)
    
    return world