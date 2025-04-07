import sys
import os
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions

file_path = 'CPN_models\\9\\RecoraList.cpn'
root = load_cpn_file(file_path)
page_block = get_page_block(root)
globbox_block = get_globbox_block(root)
data = collect_all_data(page_block, globbox_block)

print("Declarations and data successfully loaded.")
colset_functions = create_colset_functions(data["colsets"])

# Специфичные требования для данной модели: удаляем место "Names" (и дуги, связанные с ним)
net, places_info, variables = create_snakes_net(data, colset_functions, remove_names=True)

print("\nPetri Net Description:")
print(net)

print("\nPlaces and their tokens:")
for place_name, tokens, place_type in places_info:
    print(f"Place: {place_name}, Tokens: {list(tokens)}, CheckType: {place_type}")

print("\nVariables:")
for var_name, var_type in variables.items():
    print(f"Variable: {var_name}, Type: {var_type}")

net.draw("snakes_9_model/ex1.png", engine="dot")

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

# Выбор режима симуляции
print("\nSelect simulation mode:")
print("1 - Random selection of transitions")
print("2 - Manual selection (user input)")
mode = input("Enter mode (1 or 2): ").strip()

max_steps = 30
step = 0

while step < max_steps:
    available = []
    for transition in net.transition():
        modes = transition.modes()
        if modes:
            for mode_binding in modes:
                available.append((transition, mode_binding))
    if not available:
        print("\nNo more transitions can fire.")
        break

    print(f"\n--- Step {step + 1} ---")
    if mode == "1":
        # Random mode:
        transition, binding = random.choice(available)
        print(f"Randomly selected transition '{transition.name}' with binding: {binding}")
    elif mode == "2":
        # Manual mode:
        print("Available transitions:")
        for i, (t, b) in enumerate(available):
            print(f"{i}: Transition '{t.name}' with binding: {b}")
        idx = input("Enter the number of the transition to fire: ").strip()
        try:
            idx = int(idx)
            if idx < 0 or idx >= len(available):
                print("Invalid selection. Using first available transition.")
                transition, binding = available[0]
            else:
                transition, binding = available[idx]
        except:
            print("Invalid input. Using first available transition.")
            transition, binding = available[0]
    else:
        print("Unknown mode. Using random selection.")
        transition, binding = random.choice(available)
    
    print(f"Firing '{transition.name}' with binding: {binding}")
    transition.fire(binding)
    output_path = f"snakes_9_model/img/step_{step + 1}_{transition.name}.png"
    print(f"Saving snapshot to {output_path}")
    net.draw(output_path, engine="dot")
    
    step += 1

print("\nFinal state of places:")
for place in net.place():
    print(f"Place: {place.name}, Tokens: {list(place.tokens)}")
net.draw("snakes_9_model/ex2.png", engine="dot")
