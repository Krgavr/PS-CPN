from snakes.nets import Place, MultiSet, Transition, Expression, Variable, Tuple
from snakes.plugins import *
import snakes.plugins
snakes.plugins.load('gv', 'snakes.nets', 'nets')  # Load the gv plugin
from nets import PetriNet
import re

# Function to create colset functions based on file data
def create_colset_functions(colsets):
    colset_functions = {}
    for colset in colsets:
        colset_name = colset["name"]
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
    condition = condition.strip("[]")
    condition = condition.replace("<>", "!=")
    condition = condition.replace("=", "==")
    condition = condition.replace("!==", "!=")
    return condition

# Function to parse arc expressions
def parse_arc_expression(expression, arc_type):
    """
    Converts arc expressions from ML to Variable or Tuple.
    Input arcs (PtoT): Variable.
    Output arcs (TtoP): Tuple.
    """
    if not expression:
        return MultiSet()
    token_pattern = r"(\d+)`(\w+|\(.*?\))"
    if arc_type == "PtoT":
        tokens = re.findall(token_pattern, expression)
        variables = []
        for count, value in tokens:
            for _ in range(int(count)):
                variables.append(Variable(value.strip("()")))
        return variables[0] if len(variables) == 1 else MultiSet(variables)
    elif arc_type == "TtoP":
        tokens = re.findall(token_pattern, expression)
        result_tuple = []
        for count, value in tokens:
            if value.startswith("(") and value.endswith(")"):
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

    for place in data["places"]:
        place_name = place["text"]
        place_type = place["type"]
        initmark = place["initmark"]
        is_valid_func = colset_functions.get(place_type, lambda x: True)
        tokens = parse_initmark(initmark)
        net.add_place(Place(place_name, tokens=tokens, check=is_valid_func))
        places_info.append((place_name, tokens, place_type))

    for transition in data["transitions"]:
        transition_name = transition["text"]
        condition = convert_condition(transition["condition"])
        if condition:
            print(f"Adding Transition: {transition_name} with guard: {condition}")
            net.add_transition(Transition(transition_name, guard=Expression(condition)))
        else:
            print(f"Adding Transition: {transition_name} without guard")
            net.add_transition(Transition(transition_name))

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
            if isinstance(arc_label, list):
                for var in arc_label:
                    net.add_input(place_name, transition_name, var)
            else:
                net.add_input(place_name, transition_name, arc_label)
        elif arc_type == "TtoP":
            print(f"Adding output arc: {transition_name} -> {place_name} with expression {expression}")
            arc_label = parse_arc_expression(expression, arc_type)
            net.add_output(place_name, transition_name, arc_label)

    return net, places_info, variables
