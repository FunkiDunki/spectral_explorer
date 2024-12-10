'''
Purpose: This file contains the main logic for a text-based adventure game.  
It manages game flow, user interactions, and progression through various scenarios. 
'''

from openai import OpenAI
from typing import List, Type, Dict, Final
from pydantic import BaseModel, Field

TEMPERATURE: Final = 0.8
FORMAT_SPACING: Final = 10

def call_llm_unstructured(client: OpenAI, model: str, messages: List, temperature=TEMPERATURE) -> str:
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

def update_json_schema(input_model: Type[BaseModel]) -> Dict[str, any]:
    '''
    new update to lmstudio has stricter reqs for structured_output:
    '''
    tmp = input_model.model_json_schema()

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "test_schema",
            "strict": True,
            "schema": tmp,
        }
    }

def call_llm_structured(client: OpenAI, model: str, messages: List, model_format: Type[BaseModel], temperature=TEMPERATURE, update_schema: bool = False):
    '''
    Make api call to create an object with specified format, as a response from llm.
    '''

    #first get the schema for the model:
    if update_schema:
        schema = update_json_schema(model_format)
    else:
        schema = model_format

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
    """
    Generates the main historical background of a fictional world based on the user's story prompt.
    Args:
        story_prompt (str): A user-provided description or idea for the world.
        model (str): The model name used to interact with the language model.
        client (OpenAI): The OpenAI API client for processing the request.
    Returns:
        str: The generated history of the world as a string.
    """
    # Prepare messages for the language model with system and user roles.
    messages = [
        {"role": "system", "content": "You are a storyteller, describing the history of a world based on the user's prompt."},
        {"role": "user", "content": story_prompt},
    ]

    # Call the unstructured LLM to generate the world history.
    return call_llm_unstructured(client=client, model=model, messages=messages)


def generate_regions(world: World, model: str, client: OpenAI, update_schema: bool = False) -> World:
    """
    Generates regions for the fictional world, adding detailed descriptions and histories.
    Args:
        world (World): The world object that stores history and region information.
        model (str): The model name used to interact with the language model.
        client (OpenAI): The OpenAI API client for processing the request.
        update_schema (bool, optional): Whether to update the model schema. Defaults to False.
    Returns:
        World: The updated world object with regions added.
    """
    # Prepare the prompt that describes the task for the language model.
    prompt = (
        "For the following world, describe 2-6 overall regions that exist. "
        "For each location, give a name and a physical description of key features of the location that might hint at the rich history. "
        "Also, describe a derived history, which contains a summary of events from the world history that influenced the region. "
        "Include also any relevant descriptions of current-day life in the region. "
    )
    # Provide messages with system instructions, the task, and the world history.
    messages = [
        {"role": "system", "content": "You are a designer of fantastic world, describing a world as the user desires."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": f"{world.history}"}
    ]

    # Call the structured LLM and parse the result into RegionGenerateResponse.
    result: RegionGenerateResponse = call_llm_structured(
        client=client,
        model=model, 
        messages=messages,
        model_format=RegionGenerateResponse,
        update_schema=update_schema
    ) 

    # Add each generated region to the world object.
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


def generate_cities(world: World, model: str, client: OpenAI, update_schema: bool = False) -> World:
    """
    Generates cities (subregions) for a specific region in the world.
    Args:
        world (World): The world object containing regions and history.
        model (str): The model name used to interact with the language model.
        client (OpenAI): The OpenAI API client for processing the request.
        update_schema (bool, optional): Whether to update the model schema. Defaults to False.
    Returns:
        World: The updated world object with cities added to the player's region.
    """
    # Check if cities already exist for the region.
    if len(world.all_nodes[world.player.region_id].children) > 0:
        # If cities are already generated, return the world as is.
        return world
    
    # Prompt for generating sub-locations (cities) within the current region.
    prompt = (
        f"Based on the history of the world and the descriptions of the main regions, list 2-5 sub-locations that might exist within the region of {world.all_nodes[world.player.region_id].node_name}. "
        "For each location, give a name and a physical description of key features of the location that might hint at the rich history of the region it is in. "
        "Also, describe a derived history, which contains a summary of any relevant events from the history of the region it is in. "
        "Include also any relevant descriptions of current-day life in the subregion. "
        "Don't generate a subregion named after the region it is in. "
    )
    # Retrieve relevant world information while excluding its overall history.
    info = get_relevant_information(world, exclusions=["history"])
    messages = [
        {"role": "system", "content": "You are a designer of fantastic world, expanding on how the regions and subregions connect to the world's story."},
        {"role": "user", "content": prompt},
        *info,
    ]

    # Call the structured LLM and parse the result into SubRegionGenerateResponse.
    result: SubRegionGenerateResponse = call_llm_structured(client, model, messages, SubRegionGenerateResponse, update_schema=update_schema) 

    # Add each generated city (subregion) to the current region.
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


def place_player_region(world: World, print_output, get_input) -> World:
    """
    Places the player into a region of their choosing to explore.
    Args:
        world (World): The game world object.
        print_output: Function to display text to the user.
        get_input: Function to capture user input.
    Returns:
        World: Updated world object with the player's chosen region.
    """
    # Display the list of main regions in the world.
    print_output(f"In this world, there are {len(world.regions)} main regions:")
    for i, region in enumerate(world.regions):
        print_output(f"\t({i+1}). {world.all_nodes[region].node_name}")
    
    # Prompt the user to choose a region.
    choice = get_input("Pick the number of a region to explore!: ")
    
    # Validate the input: ensure it is numeric and within the valid range.
    while not (choice.isnumeric() and int(choice) >= 1 and int(choice) <= len(world.regions)):
        print_output("Whoops, that wasn't a valid choice!")
        choice = get_input("Pick the number of a region to explore!: ")
    
    # Convert choice to zero-based index for list access.
    choice = int(choice) - 1

    # Confirm the chosen region and update the player's current region.
    print_output(f"Okay! Let's explore {world.all_nodes[world.regions[choice]].node_name}!")
    world.player.region_id = world.regions[choice]

    return world


def get_relevant_information(world: World, exclusions: List[str] = []) -> List[dict]:
    """
    Gathers relevant game state information for generating prompts.
    Args:
        world (World): The game world object.
        exclusions (List[str]): List of exclusions, e.g., "history" to omit historical details.
    Returns:
        List[dict]: A list of dictionaries containing relevant information.
    """
    result = []

    # Include full history of the world unless excluded.
    if "history" not in exclusions:
        result.append({"role": "user", "content": f"Here is the full history of the world: {world.history}"})

    # Check if the player is located in a valid region.
    if world.player.region_id != -1:
        # Gather information about all regions.
        regions_info = [
            {
                "name": world.all_nodes[region].node_name,
                "description": world.all_nodes[region].node_description,
                "connection_to_history": world.all_nodes[region].derived_history,
                "current_dynamics": world.all_nodes[region].current_dynamics,
            }
            for region in world.regions
        ]
        result.append({"role": "user", "content": f"There are a few main regions of the world: {regions_info}"})

        # Add information about the player's current region.
        result.append(
            {"role": "user", "content": f"The player is in the main region of {world.all_nodes[world.player.region_id].node_name}"}
        )

        # Check if the player is in a valid subregion.
        if world.player.subregion_id != -1:
            subregions_info = [
                {
                    "name": world.all_nodes[region].node_name,
                    "description": world.all_nodes[region].node_description,
                    "connection_to_history_of_region": world.all_nodes[region].derived_history,
                    "current_dynamics": world.all_nodes[region].current_dynamics,
                }
                for region in world.all_nodes[world.player.region_id].children
            ]
            result.append(
                {"role": "user", "content": f"Here are all generated subregions for this region so far: {subregions_info}"}
            )
            result.append(
                {"role": "user", "content": f"The player is in the subregion called {world.all_nodes[world.player.subregion_id].node_name}"}
            )

    return result


def place_player_subregion(world: World, print_output, get_input) -> World:
    """
    Places the player into a subregion of their choosing to explore.
    Args:
        world (World): The game world object.
        print_output: Function to display text to the user.
        get_input: Function to capture user input.
    Returns:
        World: Updated world object with the player's chosen subregion.
    """
    # Retrieve the current region where the player is located.
    region = world.all_nodes[world.player.region_id]

    # Display the list of subregions in the current region.
    print_output(f"In this region, there are {len(region.children)} subregions:")
    for i, subregion in enumerate(region.children):
        print_output(f"\t({i+1}). {world.all_nodes[subregion].node_name}")

    # Prompt the user to choose a subregion.
    choice = get_input("Pick the number of a subregion to explore!: ")
    
    # Validate the input: ensure it is numeric and within the valid range.
    while not (choice.isnumeric() and int(choice) >= 1 and int(choice) <= len(region.children)):
        print_output("Whoops, that wasn't a valid choice!")
        choice = get_input("Pick the number of a subregion to explore!: ")
    
    # Convert choice to zero-based index.
    choice = int(choice) - 1

    # Confirm the chosen subregion and update the player's subregion.
    print_output(f"Okay! Let's explore {world.all_nodes[region.children[choice]].node_name}!")
    world.player.subregion_id = region.children[choice]

    return world


def explore_subregion(world: World, model: str, client: OpenAI, print_output, get_input) -> World:
    """
    Allows the player to explore a subregion with looping behavior until they decide to move.
    Args:
        world (World): The game world object.
        model (str): The AI model to generate descriptions.
        client (OpenAI): The OpenAI API client.
        print_output: Function to display text to the user.
        get_input: Function to capture user input.
    Returns:
        World: Updated world object after exploration.
    """
    # Get the current subregion.
    subregion = world.all_nodes[world.player.subregion_id]

    # Gather relevant information to include in the prompt.
    relevant_info = get_relevant_information(world, exclusions=["history"])

    # Create an introduction prompt for the AI.
    intro_prompt = (
        "The player is a wandering traveler, exploring various regions of the world. "
        f"They have entered the {subregion.node_name}. Describe the subregion as if the "
        "player is just entering the subregion. "
        "Don't describe the full history of the region. Instead, focus on "
        "truly painting the scene vividly, including all that the player might see as they enter the region. "
    )

    # Construct the messages for the AI model.
    messages = [
        {"role": "system", "content": "You are a storyteller, helping the player explore the given world and discover its history."},
        {"role": "system", "content": "Provide immersive, vivid descriptions of the world and its events. Avoid explicitly prompting the player with 'What would you like to do next?' or listing possible actions."},
        *relevant_info,
        {"role": "user", "content": intro_prompt},
    ]

    # Display the name of the subregion.
    print_output(('* ' * FORMAT_SPACING) + f"{subregion.node_name}" + (' *' * FORMAT_SPACING))

    # Loop until the player decides to move.
    while True:
        # Generate AI response.
        result = call_llm_unstructured(client=client, model=model, messages=messages)
        print_output(result)
        messages.append({"role": "assistant", "content": result})

        # Ask the player for their next action.
        choice = get_input("\nHow do you explore? Type 'move' to move to another region.\n>>> ").lower()
        messages.append({"role": "user", "content": f"The player said: {choice}"})

        if choice == "move":
            break  # Exit the loop if the player wants to move.

    print_output(('* ' * FORMAT_SPACING) + f"left {subregion.node_name}" + (' *' * FORMAT_SPACING))
    return world


def help_player_move(world: World, model: str, client: OpenAI, print_output, get_input, update_schema: bool = False) -> World:
    """
    Helps the player decide where to move: either to another subregion or region.
    Args:
        world (World): The game world object.
        model (str): The AI model for generation.
        client (OpenAI): The OpenAI API client.
        print_output: Function to display text to the user.
        get_input: Function to capture user input.
        update_schema (bool): Flag to update the schema if needed.
    Returns:
        World: Updated world object with the player's new location.
    """
    selection = None

    # Loop until the player chooses "region" or "subregion."
    while selection is None:
        choice = get_input(
            f"Would you like to move to another subregion in {world.all_nodes[world.player.region_id].node_name}, or change regions?\n('region' or 'subregion') >>> "
        ).lower()

        if choice == 'region':
            selection = 'region'
        elif choice == 'subregion':
            selection = 'subregion'
        else:
            print_output("Sorry, that's not a valid choice!")

    # Move based on the player's selection.
    if selection == 'subregion':
        world = place_player_subregion(world, print_output, get_input)
    elif selection == 'region':
        world = place_player_region(world, print_output, get_input)
        world = generate_cities(world, model, client, update_schema=update_schema)
        world = place_player_subregion(world, print_output, get_input)
    
    return world
