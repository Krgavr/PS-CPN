import sys
import os
import random
import logging
import shutil

# Add the parent directory to the module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions

# --- Configuring the logger: to console and to file at the same time ---
logger = logging.getLogger("simulation")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Clearing the log file (mode 'w' automatically overwrites the file)
file_handler = logging.FileHandler("snakes_2_model/simulation_log.txt", mode='w', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Customize the output to the console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# --- Clearing the image folder ---
img_folder = os.path.join("snakes_2_model", "img")
if os.path.exists(img_folder):
    # Delete the folder and re-create it (to make sure it's empty)
    shutil.rmtree(img_folder)
os.makedirs(img_folder)

# --- Loading and parsing the model ---
file_path = 'CPN_models\\2\\2-10NondeterministicProtocol.cpn'
root = load_cpn_file(file_path)
page_block = get_page_block(root)
globbox_block = get_globbox_block(root)
data = collect_all_data(page_block, globbox_block)

logger.info("Declarations and data successfully loaded.")
colset_functions = create_colset_functions(data["colsets"])
net, places_info, variables = create_snakes_net(data, colset_functions)

logger.info("\nPetri Net Description:")
logger.info(f"{net}")

logger.info("\nPlaces and their tokens:")
for place_name, tokens, place_type in places_info:
    logger.info(f"Place: {place_name}, Tokens: {list(tokens)}, CheckType: {place_type}")

logger.info("\nVariables:")
for var_name, var_type in variables.items():
    logger.info(f"Variable: {var_name}, Type: {var_type}")

# Save the first drawing of the network
net.draw("snakes_2_model/ex1.png", engine="dot")

logger.info("\n=== Full Petri Net Description ===")
logger.info("\nPlaces:")
for place in net.place():
    logger.info(f"Place: {place.name}, Tokens: {list(place.tokens)}, Check: {place.check.__name__}")
logger.info("\nTransitions:")
for transition in net.transition():
    logger.info(f"Transition: {transition.name}, Guard: {transition.guard}")
logger.info("\nArcs:")
for transition in net.transition():
    for place, arc_label in transition.input():
        logger.info(f"Input Arc: {place.name} -> {transition.name}, Label: {arc_label}")
    for place, arc_label in transition.output():
        logger.info(f"Output Arc: {transition.name} -> {place.name}, Label: {arc_label}")


# --- External logic to emulate if-then-else conditions ---
def should_fire_special_case(transition_name, binding):
    """
    Emulates the logic of conditional constructs:
      - For 'Receive Ack': the condition if success then ... is realized randomly.
      - For 'Transmit Packet': similar random logic (1 - succeeds, 0 - fails).
      - If the binding contains 'n' and 'k', it is additionally checked that n==k.
    """
    if transition_name == "Receive Ack":
        decision = random.randint(0, 1)
        logger.info(f"Simulated random success for '{transition_name}' → {decision}")
        return decision == 1

    if transition_name == "Transmit Packet":
        decision = random.randint(0, 1)
        logger.info(f"Simulated random decision for '{transition_name}' → {decision}")
        return decision == 1

    if "n" in binding and "k" in binding:
        n = binding["n"]
        k = binding["k"]
        if n != k:
            logger.info(f"'{transition_name}': n ≠ k ({n} ≠ {k}) — skipping transition")
            return False

    return True


def alternative_action(transition, binding):
    """
    Alternative action when the if-then-else condition is not met.
    Here imitation of token return to the initial place is realized.
    """
    logger.info(f"Alternative action for '{transition.name}': token returns to its original place (simulated).")


# --- Выбор режима симуляции ---
mode = ""
while mode not in ("a", "m"):
    mode = input("Select the simulation mode: (a) automatic, (m) manual: ").strip().lower()

logger.info(f"Selected simulation mode: {'Automatic' if mode=='a' else 'Manual'}")

# --- Simulation loop ---
logger.info("\nStarting simulation loop...")

max_steps = 600
step = 0

while step < max_steps:
    logger.info(f"\n--- Step {step + 1} ---")
    
    available = []
    for transition in net.transition():
        modes = transition.modes()
        if modes:
            for mode_binding in modes:
                available.append((transition, mode_binding))
    
    if not available:
        logger.info("No more transitions can fire.")
        break

    # Selects the transition depending on the mode:
    if mode == "a":
        # Automatic selection: random pair
        chosen = random.choice(available)
    else:
        # Manual selection: display all available transitions with indices
        logger.info("Available transitions:")
        for idx, (tr, binding) in enumerate(available):
            logger.info(f"{idx}: {tr.name} with binding {binding}")
        valid_input = False
        while not valid_input:
            try:
                idx_choice = int(input("Enter the number of the selected transition: "))
                if 0 <= idx_choice < len(available):
                    valid_input = True
                else:
                    logger.info("Incorrect index, try again.")
            except ValueError:
                logger.info("Enter the correct number.")
        chosen = available[idx_choice]

    transition, binding = chosen

    if should_fire_special_case(transition.name, binding):
        logger.info(f"Firing '{transition.name}' with binding: {binding}")
        transition.fire(binding)
        output_path = f"snakes_2_model/img/step_{step + 1}_{transition.name}.png"
        logger.info(f"Saving snapshot to {output_path}")
        net.draw(output_path, engine="dot")
    else:
        logger.info(f"Condition not met for '{transition.name}', executing alternative branch.")
        alternative_action(transition, binding)

    step += 1

logger.info("\nFinal state of places:")
for place in net.place():
    logger.info(f"Place: {place.name}, Tokens: {list(place.tokens)}")

net.draw("snakes_2_model/ex2.png", engine="dot")
