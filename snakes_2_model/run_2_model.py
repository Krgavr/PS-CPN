import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions

file_path = 'CPN_models\\2\\2-10NondeterministicProtocol.cpn'

# Загрузка и парсинг модели
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


# --- External logic to emulate if-then-else conditions ---
def should_fire_special_case(transition_name, binding):
    """
    Эмулирует логику условных конструкций:
      - Для 'ReceiveAck': условие if success then ... реализуется случайно.
      - Для 'TransmitPacket': аналогичная случайная логика (1 – срабатывает, 0 – не срабатывает).
      - Если binding содержит 'n' и 'k', дополнительно проверяется, что n==k.
    """
    if transition_name == "ReceiveAck":
        decision = random.randint(0, 1)
        print(f"Simulated random success for '{transition_name}' → {decision}")
        return decision == 1

    if transition_name == "TransmitPacket":
        decision = random.randint(0, 1)
        print(f"Simulated random decision for '{transition_name}' → {decision}")
        return decision == 1

    if "n" in binding and "k" in binding:
        n = binding["n"]
        k = binding["k"]
        if n != k:
            print(f"'{transition_name}': n ≠ k ({n} ≠ {k}) — skipping transition")
            return False

    return True


def alternative_action(transition, binding):
    """
    Альтернативное действие, когда условие if-then-else не выполнено.
    В данном примере просто выводится сообщение, имитирующее возврат токена на исходное место.
    При необходимости можно расширить эту функцию для вызова специального перехода.
    """
    print(f"Alternative action for '{transition.name}': token returns to its original place (simulated).")


# --- Simulation loop ---
print("\nStarting simulation loop...")

max_steps = 600
step = 0

while step < max_steps:
    print(f"\n--- Step {step + 1} ---")
    available = []
    for transition in net.transition():
        modes = transition.modes()
        if modes:
            for mode in modes:
                available.append((transition, mode))
    if available:
        transition, binding = random.choice(available)
        if should_fire_special_case(transition.name, binding):
            print(f"Firing '{transition.name}' with binding: {binding}")
            transition.fire(binding)
            output_path = f"snakes_2_model/img/step_{step + 1}_{transition.name}.png"
            print(f"Saving snapshot to {output_path}")
            net.draw(output_path, engine="dot")
        else:
            print(f"Condition not met for '{transition.name}', executing alternative branch.")
            alternative_action(transition, binding)
    else:
        print("No more transitions can fire.")
        break
    step += 1

print("\nFinal state of places:")
for place in net.place():
    print(f"Place: {place.name}, Tokens: {list(place.tokens)}")

net.draw("snakes_2_model/ex2.png", engine="dot")
