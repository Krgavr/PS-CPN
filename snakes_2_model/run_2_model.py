import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions



file_path = 'CPN_models\\2\\2-10NondeterministicProtocol.cpn'

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

net.draw("snakes_2_model/ex1.png", engine="dot")

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

print("\nStarting simulation loop...")

max_steps = 30  # let's restrict it in order not to get into an infinite loop
step = 0

while step < max_steps:
    print(f"\n--- Step {step + 1} ---")
    
    # Collect a list of all transitions with their possible bindings
    available = []
    for transition in net.transition():
        modes = transition.modes()
        if modes:
            for mode in modes:
                available.append((transition, mode))
    
    if available:
        # Randomly select a pair (transition, binding)
        chosen_transition, binding = random.choice(available)
        print(f"Transition '{chosen_transition.name}' can fire with binding: {binding}")
        chosen_transition.fire(binding)
        
        # Save a snapshot of the network status
        output_path = f"snakes_2_model/img/step_{step + 1}_{chosen_transition.name}.png"
        print(f"Saving snapshot to {output_path}")
        net.draw(output_path, engine="dot")
    else:
        print("No more transitions can fire.")
        break

    step += 1

print("\nFinal state of places:")
for place in net.place():
    print(f"Place: {place.name}, Tokens: {list(place.tokens)}")

net.draw("snakes_2_model/ex2.png", engine="dot")
