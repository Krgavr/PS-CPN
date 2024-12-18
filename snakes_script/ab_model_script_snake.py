from snakes.nets import PetriNet, Place, MultiSet, Transition, Expression, Variable, Tuple
from snakes.plugins import *
import re
import sys
import os
import snakes.plugins
snakes.plugins.load('gv', 'snakes.nets', 'nets')  # Load the gv plugin
from nets import PetriNet, Place, Transition, Variable, Expression

# Add the root path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Function to create colset functions based on file data
def create_colset_functions(colsets):
    colset_functions = {}

    for colset in colsets:
        colset_name = colset["název"]
        colset_type = colset["subtype"]
        subtype_contents = colset["subtype_contents"]

        if colset_type == "unit":
            colset_functions[colset_name] = lambda x: x == "unit"
        elif colset_type == "bool":
            colset_functions[colset_name] = lambda x: isinstance(x, bool)
        elif colset_type == "int":
            colset_functions[colset_name] = lambda x: isinstance(x, int)
        elif colset_type == "enum" and subtype_contents:
            colset_functions[colset_name] = lambda x, values=subtype_contents: x in values
        elif colset_type == "product" and subtype_contents:
            colset_functions[colset_name] = lambda x, types=subtype_contents: isinstance(x, tuple) and len(x) == len(types)
        elif colset_type == "string":
            colset_functions[colset_name] = lambda x: isinstance(x, str)
        else:
            colset_functions[colset_name] = lambda x: True  # Default check passes

    return colset_functions

# Function to parse initmark into MultiSet
def parse_initmark(initmark):
    if not initmark:
        return MultiSet()

    token_pattern = r"(\d+)`(\w+)"
    tokens = re.findall(token_pattern, initmark)
    flattened_tokens = []

    for count, value in tokens:
        flattened_tokens.extend([value] * int(count))

    return MultiSet(flattened_tokens)

# Function to create variables
def create_variables(data):
    variables = {}
    for var in data["variables"]:
        var_names = var["names"]
        var_type = var["type"]
        variables.update({name: var_type for name in var_names})
    return variables

# Function to convert ML-style conditions into Python
def convert_condition(condition):
    """
    Converts ML conditions to Python.
    Example:
        [in1<>in2] -> in1 != in2
    """
    if not condition:
        return None
    
    # Remove square brackets
    condition = condition.strip("[]")
    
    # Replace ML symbols with Python equivalents
    condition = condition.replace("<>", "!=")  # Replace <>
    condition = condition.replace("=", "==")   # Replace = with ==
    condition = condition.replace("!==", "!=")  # Protect from replacement errors

    return condition

# Function to parse arc expressions
def parse_arc_expression(expression, arc_type):
    """
    Converts arc expressions from ML to Variable or Tuple.
    Input arcs (PtoT): Variable.
    Output arcs (TtoP): Tuple.

    Example:
        '1`in1' -> Variable('in1') for PtoT
        '1`(in1,in2)' -> Tuple([Variable('in1'), Variable('in2')]) for TtoP
    """
    if not expression:
        return MultiSet()

    token_pattern = r"(\d+)`(\w+|\(.*?\))"  # Match expressions and variables

    if arc_type == "PtoT":  # Input arcs
        tokens = re.findall(token_pattern, expression)
        variables = []
        for count, value in tokens:
            for _ in range(int(count)):
                variables.append(Variable(value.strip("()")))  # Add as variable
        return variables[0] if len(variables) == 1 else MultiSet(variables)

    elif arc_type == "TtoP":  # Output arcs
        tokens = re.findall(token_pattern, expression)
        result_tuple = []

        for count, value in tokens:
            if value.startswith("(") and value.endswith(")"):
                # Split tuple into individual variables
                tuple_variables = [Variable(v.strip()) for v in value[1:-1].split(",")]
                result_tuple.extend([tuple_variables] * int(count))
            else:
                result_tuple.append(Variable(value))

        return Tuple(result_tuple[0]) if len(result_tuple) == 1 else result_tuple

# Main function to create a Petri net
def create_snakes_net(data, colset_functions):
    net = PetriNet("CPN_Model")
    places_info = []
    variables = create_variables(data)

    # Add places
    for place in data["places"]:
        place_name = place["text"]
        place_type = place["type"]
        initmark = place["initmark"]

        is_valid_func = colset_functions.get(place_type, lambda x: True)
        tokens = parse_initmark(initmark)

        net.add_place(Place(place_name, tokens=tokens, check=is_valid_func))
        places_info.append((place_name, tokens, place_type))

    # Add transitions with conditions
    for transition in data["transitions"]:
        transition_name = transition["text"]
        condition = convert_condition(transition["condition"])

        if condition:
            print(f"Adding Transition: {transition_name} with guard: {condition}")
            net.add_transition(Transition(transition_name, guard=Expression(condition)))
        else:
            print(f"Adding Transition: {transition_name} without guard")
            net.add_transition(Transition(transition_name))

    # Add arcs
    for arc in data["arcs"]:
        arc_type = arc["orientation"]
        place_id = arc["placeend"]
        transition_id = arc["transend"]
        expression = arc["expression"]

        place_name = next((p["text"] for p in data["places"] if p["place_id"] == place_id), None)
        transition_name = next((t["text"] for t in data["transitions"] if t["transition_id"] == transition_id), None)

        if not place_name or not transition_name:
            continue

        if arc_type == "PtoT":
            print(f"Adding input arc: {place_name} -> {transition_name} with expression {expression}")
            arc_label = parse_arc_expression(expression, arc_type)
            if isinstance(arc_label, list):  # Multiple variables
                for var in arc_label:
                    net.add_input(place_name, transition_name, var)
            else:  # Single variable
                net.add_input(place_name, transition_name, arc_label)

        elif arc_type == "TtoP":
            print(f"Adding output arc: {transition_name} -> {place_name} with expression {expression}")
            arc_label = parse_arc_expression(expression, arc_type)
            net.add_output(place_name, transition_name, arc_label)

    return net, places_info, variables

# Main program
if __name__ == "__main__":
    from parsing_AB_model.parsing_ABmodel import collect_all_data, load_cpn_file, get_page_block, get_globbox_block

    file_path = 'parsing_AB_model/model_AB.cpn'

    root = load_cpn_file(file_path)
    page_block = get_page_block(root)
    globbox_block = get_globbox_block(root)
    data = collect_all_data(page_block, globbox_block)

    print("Declarations and data successfully loaded.")
    colset_functions = create_colset_functions(data["colsets"])
    net, places_info, variables = create_snakes_net(data, colset_functions)

    print("\nPetri Net Description:")
    print(net)

    print("\nPlaces and their tokens:")
    for place_name, tokens, place_type in places_info:
        print(f"Place: {place_name}, Tokens: {list(tokens)}, CheckType: {place_type}")

    print("\nVariables:")
    for var_name, var_type in variables.items():
        print(f"Variable: {var_name}, Type: {var_type}")

    net.draw("ex1.png", engine="dot")

    print("\n=== Full Petri Net Description ===")

    print("\nPlaces:")
    for place in net.place():
        print(f"Place: {place.name}, Tokens: {list(place.tokens)}, Check: {place.check.__name__}")

    print("\nTransitions:")
    for transition in net.transition():
        print(f"Transition: {transition.name}, Guard: {transition.guard}")

    print("\nArcs:")
    for transition in net.transition():
        for place, arc_label in transition.input():
            print(f"Input Arc: {place.name} -> {transition.name}, Label: {arc_label}")
        for place, arc_label in transition.output():
            print(f"Output Arc: {transition.name} -> {place.name}, Label: {arc_label}")

    transition_name = "T1"
    print(f"\nAttempting to fire Transition: {transition_name}")
    try:
        transition = net.transition(transition_name)
        modes = transition.modes()
        if modes:
            print(f"Possible bindings found: {modes}")
            for binding in modes:
                print(f"Firing with binding: {binding}")
                transition.fire(binding)
                print(f"Transition '{transition_name}' fired successfully with binding: {binding}")
                break
        else:
            print(f"No available bindings for Transition '{transition_name}'")
    except Exception as e:
        print(f"Error firing Transition '{transition_name}': {e}")

    print("\nPlaces and their tokens after fire:")
    for place in net.place():
        print(f"Place: {place.name}, Tokens: {list(place.tokens)}")

    net.draw("ex2.png", engine="dot")