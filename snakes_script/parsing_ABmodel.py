import pandas as pd
from xml.etree import ElementTree as ET

def load_cpn_file(file_path):
    """
    Načte a vrátí kořenový prvek XML souboru.
    """
    try:
        tree = ET.parse(file_path)  # Načtení XML souboru
        root = tree.getroot()  # Získání kořenového elementu
        return root
    except ET.ParseError as e:
        raise ValueError(f"Chyba při zpracování XML: {e}")  # Ošetření chyby při parsování
    except FileNotFoundError:
        raise ValueError("Soubor nebyl nalezen, zkontrolujte cestu.")  # Ošetření chyby, pokud soubor neexistuje


def get_page_block(root):
    """
    Najde blok <page> uvnitř <cpnet>.
    """
    cpnet_block = root.find('cpnet')
    if cpnet_block is None:
        raise ValueError("Soubor neobsahuje blok <cpnet>.")

    page_block = cpnet_block.find('page')
    if page_block is None:
        raise ValueError("Blok <cpnet> neobsahuje <page>.")

    return page_block


def get_globbox_block(root):
    """
    Najde blok <globbox> uvnitř <cpnet>.
    """
    cpnet_block = root.find('cpnet')
    if cpnet_block is None:
        raise ValueError("Soubor neobsahuje blok <cpnet>.")
    
    globbox_block = cpnet_block.find('globbox')
    if globbox_block is None:
        # Pokud blok <globbox> neexistuje, vyvolat chybu
        raise ValueError("Soubor neobsahuje blok <globbox>.")

    return globbox_block  # Vrátit nalezený blok


def get_colsets(globbox_block):
    """
    Získání informací o barevných množinách (colsets) z bloku <globbox>.
    """
    colsets = []  # Inicializace seznamu pro barevné množiny
    for color in globbox_block.findall('.//color'):  # Najít všechny elementy <color>
        # Získání ID barevné množiny z atributu <color id="...">
        colset_id = color.attrib.get('id')  

        # Získání názvu barevné množiny z podřízeného <id>
        colset_name = color.find('id').text if color.find('id') is not None else None

        # Získání layoutu z podřízeného <layout>
        layout_element = color.find('layout')
        layout_text = layout_element.text if layout_element is not None else None

        # Určení typu (subtype) na základě prvního prvku mezi <id> a <layout>
        subtype = None  # Inicializace proměnné subtype jako None
        subtype_contents = None  # Inicializace seznamu pro obsah
        for child in color:  # Iterace přes všechny podřízené elementy v rámci <color>
            if child.tag not in ['id', 'layout']:  # Ignorujeme prvky <id> a <layout>, protože neurčují typ
                subtype = child.tag  # Používáme název tagu aktuálního prvku jako typ (např. unit, bool, enum)
                # Pokud existují prvky <id> uvnitř aktuálního podřízeného prvku, získáme jejich obsah
                subtype_contents= [elem.text for elem in child.findall('id') if elem.text]
                subtype_contents = subtype_contents if subtype_contents else None  # Pokud seznam prázdný, nastavíme None
                break  # Ukončíme smyčku, protože typ byl nalezen

        # Přidání dat barevné množiny do seznamu
        colsets.append({
            'id': colset_id,         # ID barevné množiny, jedinečný identifikátor pro konkrétní množinu
            'name': colset_name,    # Název barevné množiny z elementu <id>
            'layout': layout_text,   # Textová reprezentace množiny z elementu <layout>
            'subtype': subtype,      # Typ barevné množiny, určený na základě podřízených prvků (např. unit, enum, product)
            'subtype_contents': subtype_contents     # Obsah podřízených prvků, např. seznam hodnot (['A', 'B']) nebo None, pokud není obsah
        })


    return colsets  # Vrátit seznam barevných množin


def get_vars(globbox_block):
    """
    Získání informací o proměnných (variables) z bloku <globbox>.
    """
    vars = []  # Inicializace seznamu pro proměnné
    for var in globbox_block.findall('.//var'):  # Najít všechny elementy <var>
        # Získání ID proměnné z atributu <var id="...">
        var_id = var.attrib.get('id')

        # Získání typu proměnné z elementu <type><id>...</id></type>
        type_element = var.find('type')
        var_type = type_element.find('id').text if type_element is not None and type_element.find('id') is not None else None

        # Získání názvů proměnných z elementů <id>
        var_names = [name.text for name in var.findall('id') if name.text]

        # Získání layoutu z podřízeného <layout>
        layout_element = var.find('layout')
        layout_text = layout_element.text if layout_element is not None else None

        # Přidání dat proměnné do seznamu
        vars.append({
            'id': var_id,          # ID proměnné, jedinečný identifikátor
            'type': var_type,      # Typ proměnné (např. IN)
            'names': var_names,    # Seznam názvů proměnných
            'layout': layout_text  # Textová reprezentace z elementu <layout>
        })

    return vars  # Vrátit seznam proměnných



def get_places(page_block):
    """
    Získání informací o místech (<place>).
    """
    places = []
    for place in page_block.findall('place'):
        place_id = place.attrib.get('id')  # Získání ID místa
        text = place.find('text').text if place.find('text') is not None else None  # Získání názvu místa
        type_element = place.find('type')  # Získání typu místa
        place_type = (
            type_element.find('text').text
            if type_element is not None and type_element.find('text') is not None
            else None
        )
        initmark_element = place.find('initmark')  # Získání počáteční značky
        initmark = (
            initmark_element.find('text').text
            if initmark_element is not None and initmark_element.find('text') is not None
            else None
        )

        # Přidání dat místa do seznamu
        places.append({
            'place_id': place_id,
            'text': text,
            'type': place_type,
            'initmark': initmark
        })
    return places


def get_transitions(page_block):
    """
    Získání informací o přechodech (<trans>).
    """
    transitions = []
    for transition in page_block.findall('trans'):
        transition_id = transition.attrib.get('id')  # Získání ID přechodu
        text = transition.find('text').text if transition.find('text') is not None else None  # Získání názvu přechodu

        # Nalezení podmínky (cond)
        cond_element = transition.find('cond')
        condition = (
            cond_element.find('text').text if cond_element is not None and cond_element.find('text') is not None else None
        )  # Získání podmínky, např. [in1<>in2]

        # Nalezení časового omezení (time) a jeho extrakce
        time_element = transition.find('time')
        time_text = (
            time_element.find('text').text if time_element is not None and time_element.find('text') is not None else None
        )

        # Nalezení kódu (code) a jeho extrakce
        code_element = transition.find('code')
        code_text = (
            code_element.find('text').text if code_element is not None and code_element.find('text') is not None else None
        )

        # Nalezení priority (priority) a její extrakce
        priority_element = transition.find('priority')
        priority_text = (
            priority_element.find('text').text if priority_element is not None and priority_element.find('text') is not None else None
        )

        # Přidání dat přechodu do seznamu
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
    Získání informací o hranách (<arc>).
    """
    arcs = []
    for arc in page_block.findall('arc'):
        arc_id = arc.attrib.get('id')  # Získání ID hrany
        orientation = arc.attrib.get('orientation')  # Získání směru hrany (např. "PtoT")
        order = arc.attrib.get('order')  # Získání pořadí hrany (např. "1")

        # Získání ID přechodu a místa, které hrana spojuje
        transend = arc.find('transend').attrib.get('idref') if arc.find('transend') is not None else None
        placeend = arc.find('placeend').attrib.get('idref') if arc.find('placeend') is not None else None

        # Získání výrazu hrany
        expression_element = arc.find('annot/text')  # Hledání anotace výrazu
        expression = expression_element.text if expression_element is not None else None

        # Přidání dat hrany do seznamu
        arcs.append({
            'arc_id': arc_id,          # ID hrany
            'orientation': orientation,  # Směr (např. "PtoT" nebo "TtoP")
            'order': order,            # Pořadí hrany
            'transend': transend,      # ID přechodu
            'placeend': placeend,      # ID místa
            'expression': expression   # Výraz (např. "1`in2")
        })
    return arcs


def collect_all_data(page_block, globbox_block):
    """
    Sbírá všechna data (místa, přechody, oblouky) a spojuje je do jednoho slovníku.
    """
    parsed_data = {
        "places": get_places(page_block),
        "transitions": get_transitions(page_block),
        "arcs": get_arcs(page_block),
        "colsets": get_colsets(globbox_block),
        "variables": get_vars(globbox_block)
    }

    return parsed_data


if __name__ == "__main__":
    # Hlavní program
    file_path = 'parsing_AB_model/model_AB.cpn'

    # Načtení souboru
    root = load_cpn_file(file_path)

    # Nalezení bloku <page>
    page_block = get_page_block(root)

    # Nalezení bloku <globbox>
    globbox_block = get_globbox_block(root)


    # Shromáždění všech dat do slovníku
    all_data = collect_all_data(page_block, globbox_block)

    # Převod dat na DataFrame
    places_df = pd.DataFrame(all_data["places"])  # Data o místech
    transitions_df = pd.DataFrame(all_data["transitions"])  # Data o přechodech
    arcs_df = pd.DataFrame(all_data["arcs"])  # Data o hranách
    colsets_df = pd.DataFrame(all_data["colsets"])
    variables_df = pd.DataFrame(all_data["variables"])

    # Načítání rámce DataFrame do konzoly
    print("Informace o místech:")
    print(places_df)

    print("\nInformace o přechodech:")
    print(transitions_df)

    print("\nInformace o hranách:")
    print(arcs_df)

    print("\nInformace o colsetech:")
    print(colsets_df)

    print("\nInformace o variables:")
    print(variables_df)