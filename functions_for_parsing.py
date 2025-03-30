import pandas as pd
from xml.etree import ElementTree as ET

def load_cpn_file(file_path):
    """
    Reads and returns the root element of the XML file.
    """
    try:
        tree = ET.parse(file_path)  # Reading XML file
        root = tree.getroot()  # Getting the root element
        return root
    except ET.ParseError as e:
        raise ValueError(f"Error during XML processing: {e}")  # Parsing error handling
    except FileNotFoundError:
        raise ValueError("File not found, check path.")  # Error handling if file does not exist


def get_page_block(root):
    """
    Finds the <page> block inside <cpnet>.
    """
    cpnet_block = root.find('cpnet')
    if cpnet_block is None:
        raise ValueError("The file does not contain the <cpnet> block.")

    page_block = cpnet_block.find('page')
    if page_block is None:
        raise ValueError("The <cpnet> block does not contain <page>.")

    return page_block


def get_globbox_block(root):
    """
    Finds the <globbox> block inside <cpnet>.
    """
    cpnet_block = root.find('cpnet')
    if cpnet_block is None:
        raise ValueError("The file does not contain a <cpnet> block.")
    
    globbox_block = cpnet_block.find('globbox')
    if globbox_block is None:
        # If the <globbox> block does not exist, raise an error
        raise ValueError("The file does not contain a <globbox> block.")

    return globbox_block  # Return found block


def get_colsets(globbox_block):
    """
    Get information about colsets from <globbox> block.
    """
    colsets = []  # List initialization for colored sets
    for color in globbox_block.findall('.//color'):  # Find all elements <color>
        # Getting color set ID from <color id="..."> attribute
        colset_id = color.attrib.get('id')  

        # Getting the color set name from the child <id>
        colset_name = color.find('id').text if color.find('id') is not None else None

        # Getting layout from child <layout>
        layout_element = color.find('layout')
        layout_text = layout_element.text if layout_element is not None else None

        # Determine the type (subtype) based on the first element between <id> and <layout>
        subtype = None  # Initialize the subtype variable as None
        subtype_contents = None  # Initializing a list for content
        index_values = None  # Initialize index_values as None

        for child in color:  # Iteration over all child elements within <color>
            if child.tag not in ['id', 'layout']:  # Ignore <id> and <layout> elements because they do not specify the type
                subtype = child.tag  # We use the tag name of the current item as a type (e.g. unit, bool, enum)

                # Special handling for 'index' subtype
                if subtype == "index":
                    # Extract <ml> and <id> values
                    ml_values = [int(ml.text) for ml in child.findall('ml') if ml.text.isdigit()]
                    id_value = child.find('id').text if child.find('id') is not None else None
                    index_values = {'idx': ml_values, 'name_of_object': id_value}
                # If not 'index', gather other contents
                else:
                    # If there are <id> elements inside the current child element, we get their content
                    subtype_contents= [elem.text for elem in child.findall('id') if elem.text]
                    subtype_contents = subtype_contents if subtype_contents else None  # If the list is empty, set None
                break  # Break the loop because the type has been found

        # Adding color set data to the list
        colsets.append({
            'id': colset_id,         # Color set ID, unique identifier for a specific set
            'name': colset_name,    # Color set name from <id> element
            'layout': layout_text,   # Text representation of the set from the <layout> element
            'subtype': subtype,      # Color set type, determined by child elements (e.g. unit, enum, product)
            'subtype_contents': subtype_contents,     # Content of child elements, e.g. list of values (['A', 'B']) or None if there is no content
            'index_values': index_values  # Values specific to 'index'
        })


    return colsets  # Return list of color sets


def get_values(globbox_block):
    """
    Extracts values defined inside <ml> tags in the <globbox> block.
    """
    values = []  # List to store variable values

    for ml in globbox_block.findall('.//ml'):  # Find all <ml> elements
        # Get the text inside the <ml> element (for example, "val n = 5;")
        ml_text = ml.text.strip() if ml.text else None

        # Retrieve the 'id' attribute from the <ml> element
        ml_id = ml.attrib.get('id')

        # Extract only those lines that match the pattern “val variable_name = value;”
        if ml_text and ml_text.startswith('val') and '=' in ml_text:
            try:
                # Parse the string "val n = 5;" -> variable and value
                parts = ml_text.split('=')
                var_name = parts[0].replace('val', '').strip()  # Variable name
                var_value = parts[1].replace(';', '').strip()   # Variable value

                # Extract <layout> (if it is inside <ml>)
                layout_element = ml.find('layout')
                layout_text = layout_element.text.strip() if layout_element is not None and layout_element.text else None

                # Append the result to the list
                values.append({
                    'id': ml_id,
                    'name': var_name,
                    'value': var_value,
                    'layout': layout_text,
                })
            except IndexError:
                continue  # Skip invalid lines

    return values


def get_vars(globbox_block):
    """
    Getting information about variables from the <globbox> block.
    """
    vars = []  # List initialization for variables
    for var in globbox_block.findall('.//var'):  # Find all <var> elements
        # Getting variable ID from attribute <var id="...">
        var_id = var.attrib.get('id')

        # Getting the variable type from the <type><id>...</id></type> element
        type_element = var.find('type')
        var_type = type_element.find('id').text if type_element is not None and type_element.find('id') is not None else None

        # Getting variable names from <id> elements
        var_names = [name.text for name in var.findall('id') if name.text]

        # Getting layout from child <layout>
        layout_element = var.find('layout')
        layout_text = layout_element.text if layout_element is not None else None

        # Adding variable data to the list
        vars.append({
            'id': var_id,          # Variable ID, unique identifier
            'type': var_type,      # Variable type (e.g. IN)
            'names': var_names,    # List of variable names
            'layout': layout_text  # Text representation from <layout> element
        })

    return vars  # Return list of variables


def get_functions(globbox_block):
    """
    Extracts function definitions from <ml> tags in the <globbox> block.
    """
    functions = []  # List to store the extracted function definitions

    for ml in globbox_block.findall('.//ml'):  # Find all <ml> elements in the <globbox> block
        # Retrieve the text content of the <ml> element (e.g., "fun Chopstick(ph(i)) = ...")
        ml_text = ml.text.strip() if ml.text else None

        # Retrieve the 'id' attribute from the <ml> element
        ml_id = ml.attrib.get('id')

        # Check if the line starts with "fun", indicating a function definition
        if ml_text and ml_text.startswith('fun'):
            try:
                # Split the text into the function name and function value
                # Example: "fun Chopstick(ph(i)) = 1`cs(i) ++ 1`cs(if i = n then 1 else i+1);"
                function_name = ml_text.split('=')[0].replace('fun', '').strip()  # Extract the function name
                function_value = ml_text.split('=', 1)[1].strip().rstrip(';')      # Extract the function value and remove the semicolon

                # Retrieve the <layout> element if it exists
                layout_element = ml.find('layout')
                layout_text = layout_element.text.strip().replace('\n', ' ') if layout_element is not None and layout_element.text else None

                # Append the function information to the list as a dictionary
                functions.append({
                    'id': ml_id,
                    'name': function_name,  # The name of the function
                    'value': function_value,  # The body of the function
                    'layout': layout_text,           # Layout text if available
                })
            except IndexError:
                # Skip any invalid <ml> entries that do not match the expected format
                continue

    return functions  




def get_places(page_block):
    """
    Getting information about places (<place>).
    """
    places = []
    for place in page_block.findall('place'):
        place_id = place.attrib.get('id')  # Getting a place ID
        text = place.find('text').text.replace('\n', '') if place.find('text') is not None else None # Getting a place name
        type_element = place.find('type')  # Getting the place type
        place_type = (
            type_element.find('text').text
            if type_element is not None and type_element.find('text') is not None
            else None
        )
        initmark_element = place.find('initmark')  # Getting the initial mark
        initmark_text_element = initmark_element.find('text') if initmark_element is not None else None
        initmark = (
            initmark_text_element.text.replace('\n', '')
            if initmark_text_element is not None and initmark_text_element.text
            else None
        )


        # Adding location data to the list
        places.append({
            'place_id': place_id,
            'text': text,
            'type': place_type,
            'initmark': initmark
        })
    return places


def get_transitions(page_block):
    """
    Get information about transitions (<trans>).
    """
    transitions = []
    for transition in page_block.findall('trans'):
        transition_id = transition.attrib.get('id')  # Getting the transition ID
        text = transition.find('text').text.replace('\n', '') if transition.find('text') is not None else None  # Getting the name of the transition

        # Finding conditions (cond)
        cond_element = transition.find('cond')
        condition = (
            cond_element.find('text').text if cond_element is not None and cond_element.find('text') is not None else None
        )  # Getting a condition, e.g. [in1<>in2]

        # Finding the time constraint (time) and its extraction
        time_element = transition.find('time')
        time_text = (
            time_element.find('text').text if time_element is not None and time_element.find('text') is not None else None
        )

        # Finding the code and extracting it
        code_element = transition.find('code')
        code_text = (
            code_element.find('text').text if code_element is not None and code_element.find('text') is not None else None
        )

        # Finding priority and extracting it
        priority_element = transition.find('priority')
        priority_text = (
            priority_element.find('text').text if priority_element is not None and priority_element.find('text') is not None else None
        )

        # Adding transition dates to the list
        transitions.append({
            'transition_id': transition_id,
            'text': text,
            'condition': condition,
            'time': time_text,             
            'code': code_text,              
            'priority': priority_text
        })
    return transitions


def get_arcs(page_block):
    """
    Getting edge information (<arc>).
    """
    arcs = []
    for arc in page_block.findall('arc'):
        arc_id = arc.attrib.get('id')  # Getting arcs ID
        orientation = arc.attrib.get('orientation')  # Getting arc direction (e.g. "PtoT")
        order = arc.attrib.get('order')  # Getting the arc order (e.g. "1")

        # Getting the ID of the transition and the place that the edge connects
        transend = arc.find('transend').attrib.get('idref') if arc.find('transend') is not None else None
        placeend = arc.find('placeend').attrib.get('idref') if arc.find('placeend') is not None else None

        # Getting the edge expression
        expression_element = arc.find('annot/text')  # Search for expression annotation
        expression = expression_element.text if expression_element is not None else None

        # Adding arc data to the list
        arcs.append({
            'arc_id': arc_id,          # Arcs ID
            'orientation': orientation,  # Direction (e.g. "PtoT" or "TtoP")
            'order': order,            # Arcs order
            'transend': transend,      # Transition ID
            'placeend': placeend,      # Place ID
            'expression': expression   # Expression (e.g. "1`in2")
        })
    return arcs


def collect_all_data(page_block, globbox_block):
    """
    It collects all data (places, transitions, arcs) and combines them into one dictionary.
    """
    parsed_data = {
        "places": get_places(page_block),
        "transitions": get_transitions(page_block),
        "arcs": get_arcs(page_block),
        "colsets": get_colsets(globbox_block),
        "values": get_values(globbox_block),
        "variables": get_vars(globbox_block),
        "functions": get_functions(globbox_block)
    }

    return parsed_data
