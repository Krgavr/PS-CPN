import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from functions_for_parsing import *

if __name__ == "__main__":
    
    file_path = 'testing_input_output_arcs/tuples/tuples.cpn'

    # Loading file
    root = load_cpn_file(file_path)

    # Finding the <page> block
    page_block = get_page_block(root)

    # Finding the <globbox> block
    globbox_block = get_globbox_block(root)


    # Collecting all data into a dictionary
    all_data = collect_all_data(page_block, globbox_block)

    # Data conversion to DataFrame
    places_df = pd.DataFrame(all_data["places"])  # Place data
    transitions_df = pd.DataFrame(all_data["transitions"])  # Transition data
    arcs_df = pd.DataFrame(all_data["arcs"])  # Arc data
    colsets_df = pd.DataFrame(all_data["colsets"])
    values_df = pd.DataFrame(all_data["values"])
    variables_df = pd.DataFrame(all_data["variables"])
    functions_df = pd.DataFrame(all_data["functions"])

    # Loading a DataFrame into the console
    pd.set_option('display.max_colwidth', None)

    print("Information about places:")
    print(places_df)

    print("\nInformation about transitions:")
    print(transitions_df)

    print("\nInformation about arcs:")
    print(arcs_df)

    print("\nInformation about colsets:")
    print(colsets_df)

    print("\nInformation about values:")
    print(values_df)

    print("\nInformation about variables:")
    print(variables_df)

    print("\nInformation about functions:")
    print(functions_df)
