'''
Defaults for the runtime.
This fully default version of the runtime config needs the api-key to be replaced, if one wants to use openai endpoints.
'''
DEFAULT_RUNTIME_CONFIG= {
    'output_dir': './saves',
    'url': None,
    'api-key': 'lm-studio',
    'model': 'mistral-nemo-instruct-2407',
    'frontend-active':False ,
    'save-name': '/world.pkl',
    'story-prompt': "write about the history of a magical world called akhel. "
                "Focus on important events that might impact the world, or the citizens of it.",
    'update-schema': False, #set for true when using LM studio or if any schema problems arise
}

DEFAULT_FRONTEND_CONFIG = {
    'title': 'Spectral Explorer Example',
    'size': "1000x800",
    'show-image': False,
    'image-location': '',
    'notes-location': './notes'
}
