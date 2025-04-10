# PS-CPN

# PS-CPN Converter

A Python project that converts Colored Petri Net (CPN) models created in CPN Tools into equivalent SNAKES models. This tool parses the XML representation of CPN models, extracts critical information into Pandas DataFrames, and then builds a fully functional Petri net using the SNAKES library.

---

## Overview

The **PS-CPN Converter** automates the conversion of CPN models (from `.cpn` files) into Python-based SNAKES models. It provides a seamless way to:
- **Parse** CPN Tools models in XML format.
- **Extract and structure** model data (places, transitions, arcs, colsets, variables, etc.) using Pandas.
- **Construct** and **simulate** equivalent Petri nets in Python with SNAKES.
- **Visualize** the resulting model for analysis and further experimentation.

---

## Features

- **XML Parsing**: Reads and processes `.cpn` files to extract key model components.
- **Data Structuring**: Converts model data into Pandas DataFrames for easy inspection and manipulation.
- **SNAKES Integration**: Automatically builds Petri nets using SNAKES objects (`Place`, `Transition`, `MultiSet`, etc.).
- **Simulation Ready**: Supports basic simulation by allowing transitions to fire and inspecting token flow.
- **Visualization**: Generates graphical representations of the Petri net using the `draw()` function.

---

## Requirements

- Python 
- [SNAKES](https://snakes.ibisc.univ-evry.fr/)
- [Pandas](https://pandas.pydata.org/)
- Other common packages (e.g., `lxml`, `re`)

Install the dependencies using pip:

```bash
pip install requirements.txt
```

---

## Project Structure

```
PS-CPN/
├── CPN_models/
│   ├── ...                              # XML models
├── main_code_function/
│   ├── functions_for_parsing.py         # XML and model parsing functions
│   └── snakes_engine_main.py            # SNAKES conversion and simulation functions
├── parsing_models/
│   └── ...                              # CPN model parsing examples
├── snake_models/
│   └──...
├── README.md                            # This file
└── requirements.txt                     # Project dependencies
```

---

## Usage

1. **Parse a CPN Model**:  
   Use the provided parsing script to convert a `.cpn` file into structured data. For example:

    ```bash
    python parsing_models/parsing_1_model/parsing_1_model.py
    ```

2. **Build and Simulate the Petri Net**:  
   Run the SNAKES conversion script to build the Petri net from the parsed data:

    ```bash
    python snake_models/snakes_AB_model/run_ab_model.py
    ```

3. **Visualize the Model**:  
   The scripts automatically generate graphical representations of the Petri net. You can view these images to understand the network structure.

---

## Demonstration

During the presentation, the workflow will be demonstrated by:
- **Showing a basic CPN model** in CPN Tools.
- **Displaying the parsing process** where the XML is converted into Pandas DataFrames.
- **Converting the parsed data** to a SNAKES Petri net and visually simulating token flow by firing transitions.

---

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests. Contributions such as enhanced parsing, new visualization options, or support for additional CPN features are very welcome!

## Contact

For any questions or suggestions, please open an issue or contact the project maintainers.
