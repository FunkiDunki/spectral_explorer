# Spectral Explorer

**Spectral Explorer** is an interactive program that allows users to explore a detailed, fictional world generated by an AI model. Users can begin an adventure with their own input or a default prompt, setting the stage for the creation of a multi-layered narrative.

---

## Motivations
We set out to create a tool that could push the bounds on what is possible for AI generated text-based adventure games. We were unsatisfied with the current limitations of such experiences, and intended to address at least one of the current issues. While our project has not perfected this genre of game, it can be used as a foundation for future projects, as in this state, it can successfully generate a detailed and consistent narrative for a world that the player can explore.

---
## Features

### **Dynamic World Creation**
- Generates a fictional world with a deep and cohesive structure.  
- Key stages of generation include:
  - **World History**: Lays the foundation for the world's culture and events.  
  - **Regions**: Highlights distinct areas, each with unique characteristics and dynamics.  
  - **Sub-Regions**: Explores smaller, detailed areas within regions, enhancing immersion.

### **Interactive Exploration**
- Users can navigate and explore specific regions or sub-regions within the world.  
- Upon entering a sub-region, users receive vivid descriptions of their surroundings.  
- Interactive features allow users to:
  - Ask questions about the environment.
  - Perform actions.
  - Move to different areas.

### **Layered Context**
- Detailed context, including information about and the history of the world and important regions, is passed to the AI model at each stage of the generation process.  
- Ensures consistency and a holistic narrative across the world.  
- Addresses common issues in AI-generated text adventures, such as disjointed or unconnected storylines.

---

## Applications Beyond Gaming

The methodology used in Spectral Explorer—breaking down and contextualizing information at multiple levels—has broader implications, including:

- **AI-Driven Tutorials:**  
  Teaching complex tasks in a structured, easy-to-follow manner.  
- **Generating Structured Explanations:**  
  Providing clear, multi-layered insights across various domains.  

Spectral Explorer demonstrates the potential for AI to go beyond entertainment and contribute to education and content generation in innovative ways.

---

## Usage

- **Example Workflow with Frontend:**
  python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps spectral-explorer
  pip install openai
  pip install pillow
  pip install devtools
  Use LM studio to run llama-3.2-1b-instruct model on http://localhost:1234/v1/
  python -m examples.example_usage_visual.py

- **Example Workflow Using Terminal:**
  python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps spectral-explorer
  pip install openai
  pip install pillow
  pip install devtools
  Use LM studio to run llama-3.2-1b-instruct model on http://localhost:1234/v1/
  python -m examples.example_slim_usage.py

- **Example Workflow Using OpenAI API key:**
  python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps spectral-explorer
  pip install openai
  pip install pillow
  pip install devtools
  Use your own API key as OPENAI_KEY environment variable
  python -m examples.example_openai_usage.py
  
---

## Future Works

- **State consistency**
    This project did not address the issue of maintaining changes to the environment over time or over multiple locations. 

- **Objectives and termination conditions**
    There is currently no way to win or lose in this program and there is no clear objective.

- **Visuals**
    To further build off the use of AI to generate a text-based game, one could use the text of the game to generate AI images to act as the background of the current subregion/region.

---

## Authors and Contributors

### Authors
- **[Nicholas Hotelling]**  
  - Role: Backend Developer
  - Contributions: Implemented the heirarchical world generation system, implemented world navigation system, model tuning and prompt engineering.
  - Contact: [nicholashotelling@gmail.com] | [GitHub Profile](https://github.com/FunkiDunki)

- **[Baylor Pond]**  
  - Role: Documentation Specialist, Assistant Developer  
  - Contributions: Created README, connected backend to frontend using multi-thread approach, and assisted in project vision and implementation structure
  - Contact: [baylorpond@gmail.com] | [GitHub Profile](https://github.com/BPond4)

- **[Nicholas Perlich]**  
  - Role: Frontend Developer  
  - Contributions: Created a frontend for a better user experience and created a cohesive format to code structure and display for clear understanding and ease of adding to the code base
  - Contact: [nicholasperlich2003@gmail.com] | [GitHub Profile](https://github.com/NickPerlich)
---