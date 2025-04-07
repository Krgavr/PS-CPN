import sys
import os
import random
import logging
import shutil

# Logging setup: output to console and write to “simulation_log.txt” file
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a handler for the file (overwriting the file each time)
file_handler = logging.FileHandler("snakes_2_model/simulation_log.txt", mode="w", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Create a handler for the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Add the parent directory to the module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions_for_parsing import collect_all_data, load_cpn_file, get_page_block, get_globbox_block
from snakes_engine_main import create_snakes_net, create_colset_functions

file_path = 'CPN_models\\2\\2-10NondeterministicProtocol.cpn'

logger.info("Loading and parsing model...")
# Loading and parsing the model
root = load_cpn_file(file_path)
page_block = get_page_block(root)
globbox_block = get_globbox_block(root)
data = collect_all_data(page_block, globbox_block)

logger.info("Declarations and data successfully loaded.")
colset_functions = create_colset_functions(data["colsets"])
net, places_info, variables = create_snakes_net(data, colset_functions)

logger.info("\nPetri Net Description:")
logger.info(str(net))

logger.info("\nPlaces and their tokens:")
for place_name, tokens, place_type in places_info:
    logger.info(f"Place: {place_name}, Tokens: {list(tokens)}, CheckType: {place_type}")

logger.info("\nVariables:")
for var_name, var_type in variables.items():
    logger.info(f"Variable: {var_name}, Type: {var_type}")

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

# --- Clear the image folder before running the simulation ---
img_dir = os.path.join("snakes_2_model", "img")
if os.path.exists(img_dir):
    for filename in os.listdir(img_dir):
        file_path_full = os.path.join(img_dir, filename)
        try:
            if os.path.isfile(file_path_full) or os.path.islink(file_path_full):
                os.unlink(file_path_full)
            elif os.path.isdir(file_path_full):
                shutil.rmtree(file_path_full)
        except Exception as e:
            logger.error(f"Failed to delete {file_path_full}. Reason: {e}")
else:
    os.makedirs(img_dir)

# --- External logic to emulate if-then-else conditions ---
def should_fire_special_case(transition_name, binding):
    """
    Emulates the logic of conditional constructs:
      - For 'ReceiveAck': the condition if success then ... is realized randomly.
      - For 'TransmitPacket': similar logic - it is triggered only at a random solution.
      - If binding contains 'n' and 'k', the equality n==k is additionally checked.
    """
    if transition_name == "ReceiveAck":
        decision = random.randint(0, 1)
        logger.info(f"Simulated random success for '{transition_name}' → {decision}")
        return decision == 1

    if transition_name == "TransmitPacket":
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
    An alternative action when the if-then-else condition is not met.
    Here, a message is simply printed to simulate the token returning to its original location.
    If necessary, you can extend this function to call a special transition.
    """
    logger.info(f"Alternative action for '{transition.name}': token returns to its original place (simulated).")


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
            for mode in modes:
                available.append((transition, mode))
    if available:
        transition, binding = random.choice(available)
        if should_fire_special_case(transition.name, binding):
            logger.info(f"Firing '{transition.name}' with binding: {binding}")
            transition.fire(binding)
            output_path = f"snakes_2_model/img/step_{step + 1}_{transition.name}.png"
            logger.info(f"Saving snapshot to {output_path}")
            net.draw(output_path, engine="dot")
        else:
            logger.info(f"Condition not met for '{transition.name}', executing alternative branch.")
            alternative_action(transition, binding)
    else:
        logger.info("No more transitions can fire.")
        break
    step += 1

logger.info("\nFinal state of places:")
for place in net.place():
    logger.info(f"Place: {place.name}, Tokens: {list(place.tokens)}")

net.draw("snakes_2_model/ex2.png", engine="dot")
