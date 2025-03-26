import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions



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

net.draw("snakes_ab_model/ex1.png", engine="dot")

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

net.draw("snakes_ab_model/ex2.png", engine="dot")
