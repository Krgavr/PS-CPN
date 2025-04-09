from snakes.nets import Place, MultiSet, Transition, Expression, Variable, Tuple
from snakes.plugins import *
import snakes.plugins
snakes.plugins.load('gv', 'snakes.nets', 'nets')  # Load the gv plugin
from nets import PetriNet
import re

# Universal normalization function subtype_contents.
def normalize_subtype_contents(contents):
    if isinstance(contents, str):
        contents = contents.strip()
        if contents.startswith("[") and contents.endswith("]"):
            inner = contents[1:-1].strip()
            return [] if inner == "" else [x.strip() for x in inner.split(",")]
        else:
            return [contents]
    elif isinstance(contents, list):
        return contents
    else:
        return [contents]

# Colset type-checking functions.
def check_record(token):
    return isinstance(token, frozenset)

def check_alias(token, base_types):
    if not base_types or len(base_types) == 0:
        return True
    base = base_types[0].upper()
    if base == "INT":
        if isinstance(token, int):
            return True
        try:
            int(token)
            return True
        except:
            return False
    elif base == "STRING":
        return isinstance(token, str)
    return True

def check_list(token, base_types):
    if not isinstance(token, (list, tuple)):
        return False
    if not base_types or len(base_types) == 0:
        return True
    base = base_types[0].upper()
    if base == "STRING":
        return all(isinstance(item, str) for item in token)
    elif base == "INT":
        return all(isinstance(item, int) for item in token)
    return True

def create_colset_functions(colsets):
    colset_functions = {}
    for colset in colsets:
        colset_name = colset["name"]
        colset_type = colset["subtype"]
        subtype_contents = normalize_subtype_contents(colset.get("subtype_contents", ""))
        if colset_type == "unit":
            colset_functions[colset_name] = lambda x: x == "unit"
        elif colset_type == "bool":
            colset_functions[colset_name] = lambda x: isinstance(x, bool)
        elif colset_type == "int":
            colset_functions[colset_name] = lambda x: isinstance(x, int)
        elif colset_type.lower() == "intsum":
            colset_functions[colset_name] = lambda x: isinstance(x, int)
        elif colset_type == "enum" and subtype_contents:
            colset_functions[colset_name] = lambda x, values=subtype_contents: (str(x) if isinstance(x, Variable) else x) in values
        elif colset_type == "record":
            colset_functions[colset_name] = lambda x: check_record(x)
        elif colset_type == "alias":
            colset_functions[colset_name] = lambda x, base_types=subtype_contents: check_alias(x, base_types)
        elif colset_type == "list":
            colset_functions[colset_name] = lambda x, base_types=subtype_contents: check_list(x, base_types)
        elif colset_type.lower() == "intinf":
            colset_functions[colset_name] = lambda x: isinstance(x, int)
        elif colset_type.lower() == "time":
            colset_functions[colset_name] = lambda x: isinstance(x, (int, float))
        elif colset_type.lower() == "real":
            colset_functions[colset_name] = lambda x: isinstance(x, float)
        elif colset_type == "product" and subtype_contents:
            colset_functions[colset_name] = lambda x, types=subtype_contents: isinstance(x, tuple) and len(x) == len(types)
        elif colset_type == "string":
            colset_functions[colset_name] = lambda x: isinstance(x, str)
        else:
            colset_functions[colset_name] = lambda x: True
    return colset_functions

def parse_initmark(initmark, values_dict=None):
    if not initmark:
        return MultiSet()
    if values_dict and initmark in values_dict:
        initmark = values_dict[initmark]
    flattened_tokens = []
    parts = initmark.split("++")
    token_pattern = r"(\d+)`(.+)"  # For example: 1`(1, “COL”) or 2`B
    for part in parts:
        match = re.match(token_pattern, part.strip())
        if match:
            count = int(match.group(1))
            value = match.group(2).strip()
            if value.startswith("(") and value.endswith(")"):
                inner = value[1:-1]
                items = [v.strip() for v in re.split(r",(?![^()]*\))", inner)]
                parsed_items = []
                for item in items:
                    if item.startswith('"') and item.endswith('"'):
                        parsed_items.append(item[1:-1])
                    elif item.isdigit():
                        parsed_items.append(int(item))
                    else:
                        parsed_items.append(item)
                token = tuple(parsed_items)
            elif value.startswith("{") and value.endswith("}"):
                inner = value[1:-1].strip()
                pairs = [p.strip() for p in inner.split(",")]
                record = {}
                for pair in pairs:
                    if "=" in pair:
                        key, val = pair.split("=")
                        key = key.strip()
                        val = val.strip()
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1]
                        elif val.isdigit():
                            val = int(val)
                        record[key] = val
                token = frozenset(record.items())
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                token = tuple() if inner == "" else tuple([v.strip() for v in re.split(r',(?![^"]*")', inner)])
            else:
                if value.startswith('"') and value.endswith('"'):
                    token = value[1:-1]
                elif value.isdigit():
                    token = int(value)
                else:
                    token = value
            flattened_tokens.extend([token] * count)
        else:
            val = part.strip()
            token = tuple() if val == "[]" else val
            flattened_tokens.append(token)
    return MultiSet(flattened_tokens)

def create_variables(data):
    variables = {}
    for var in data["variables"]:
        var_names = var["names"]
        var_type = var["type"]
        variables.update({name: var_type for name in var_names})
    return variables

def convert_condition(condition):
    """
    Converts ML conditions to Python.
    Example:
        [in1<>in2] -> in1 != in2
    """
    if not condition:
        return None
    condition = condition.strip("[]").strip()
    if condition.startswith("#"):
        parts = condition.split()
        if len(parts) >= 3:
            field = parts[0][1:]
            var = parts[1]
            rest = " ".join(parts[2:])
            return f"dict({var})['{field}'] {rest}"
    condition = condition.replace("<>", "!=")
    condition = condition.replace("!==", "!=")
    condition = re.sub(r'(?<![!<>=])=(?![=])', "==", condition)
    return condition

def convert_ml_if_expression(expr):
    expr = expr.replace("^", "+")
    if_match = re.match(r"if (.+?) then (.+?) else (.+)", expr)
    if if_match:
        condition = if_match.group(1).strip()
        then_expr = if_match.group(2).strip()
        else_expr = if_match.group(3).strip()
        condition = re.sub(r"(?<![=!])=(?!=)", "==", condition)
        then = parse_token_expression(then_expr)
        else_ = "[]" if else_expr == "empty" else parse_token_expression(else_expr)
        return f"({then} if {condition} else {else_})"
    return expr

def parse_token_expression(expr):
    token_pattern = r"(\d+)`(.+)"
    match = re.match(token_pattern, expr)
    if match:
        count = int(match.group(1))
        value = match.group(2).strip()
        return f"[{value}]*{count}"
    return expr.replace("^", "+")

def convert_expression(expr):
    pattern = r"#(\w+)\s+(\w+)"
    def repl(match):
        field = match.group(1)
        var = match.group(2)
        return f"dict({var})['{field}']"
    return re.sub(pattern, repl, expr)

def parse_arc_expression(expression, arc_type):
    if not expression:
        return None
    expression = expression.strip()
    if expression.startswith("if") and "then" in expression and "else" in expression:
        if_match = re.match(r"if .+? then (.+?) else .+", expression)
        if if_match:
            then_expr = if_match.group(1).strip()
            return parse_arc_expression(then_expr, arc_type)
    if expression == "empty":
        return MultiSet()
    if "::" in expression:
        parts = [p.strip() for p in expression.split("::")]
        parts = [p.replace("#name", "").strip() for p in parts]
        return Tuple([Variable(p) for p in parts])
    token_pattern = r"(\d+)`(.+)"
    match = re.match(token_pattern, expression)
    if match:
        count = int(match.group(1))
        value = match.group(2).strip()
    else:
        value = expression
    if '^' in value:
        value = value.replace("^", "+")
        return Expression(value)
    # If the string starts with “(” and ends with “)”:
    if value.startswith("(") and value.endswith(")"):
        inner = value[1:-1].strip()
        if "," in inner:
            items = [i.strip() for i in inner.split(",")]
            return Tuple([Variable(i) for i in items])
        else:
            return Variable(inner)
    if re.search(r"[+*/-]", value):
        value = convert_expression(value)
        return Expression(value)
    return Variable(value)

def create_snakes_net(data, colset_functions, remove_names=False):
    net = PetriNet("CPN_Model")
    places_info = []
    values_dict = {val["name"]: val["value"] for val in data.get("values", [])}
    variables = create_variables(data)
    # Create places (if remove_names=True, the “Names” place is not added)
    for place in data["places"]:
        if remove_names and str(place["text"]) == "Names":
            continue
        place_name = str(place["text"])
        place_type = place["type"]
        initmark = place["initmark"]
        is_valid_func = colset_functions.get(place_type, lambda x: True)
        tokens = parse_initmark(initmark, values_dict)
        if place_type == "INTsum":
            new_tokens = []
            for t in tokens:
                if isinstance(t, str) and t.isdigit():
                    new_tokens.append(int(t))
                else:
                    new_tokens.append(t)
            tokens = MultiSet(new_tokens)
        net.add_place(Place(place_name, tokens=tokens, check=is_valid_func))
        places_info.append((place_name, tokens, place_type))
    # Create transitions
    for transition in data["transitions"]:
        transition_name = str(transition["text"])
        condition = convert_condition(transition["condition"])
        if condition:
            net.add_transition(Transition(transition_name, guard=Expression(condition)))
        else:
            net.add_transition(Transition(transition_name))
    # Create arcs (if remove_names=True, arcs related to “Names” are not added)
    places_dict = {p["place_id"]: str(p["text"]) for p in data["places"] if not (remove_names and str(p["text"])=="Names")}
    transitions_dict = {t["transition_id"]: str(t["text"]) for t in data["transitions"]}
    for arc in data["arcs"]:
        arc_type = arc["orientation"]
        place_id = arc["placeend"]
        transition_id = arc["transend"]
        expression = arc["expression"]
        place_name = places_dict.get(place_id)
        transition_name = transitions_dict.get(transition_id)
        if not place_name or not transition_name:
            continue
        arc_label = parse_arc_expression(expression, arc_type)
        if arc_type == "PtoT":
            net.add_input(place_name, transition_name, arc_label)
        elif arc_type == "TtoP":
            net.add_output(place_name, transition_name, arc_label)
        elif arc_type == "BOTHDIR":
            net.add_input(place_name, transition_name, arc_label)
            net.add_output(place_name, transition_name, arc_label)
    return net, places_info, variables