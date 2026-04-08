import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- FUNZIONI DI SUPPORTO ---

def process_inline_tags(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'([\u0370-\u03ff]+(?:[\s,.;:][\u0370-\u03ff]+)*)', r'<span xml:lang="grc">\1</span>', text)
    text = re.sub(r'_(.*?)_', r'<hi rend="italic">\1</hi>', text)
    text = re.sub(r'\[c\](.*?)\[/c\]', r'<span rend="align-center">\1</span>', text)
    text = re.sub(r'\[l\](.*?)\[/l\]', r'<span rend="align-left">\1</span>', text)
    text = re.sub(r'\[r\](.*?)\[/r\]', r'<span rend="align-right">\1</span>', text)
    text = re.sub(r'\[u\](.*?)\[/u\]', r'<span type="float-under">\1</span>', text)
    text = re.sub(r'\[a\](.*?)\[/a\]', r'<span type="float-above">\1</span>', text)
    return text

def inject_xml_content(parent_element, xml_string, tei_ns):
    try:
        temp_xml = f'<temp xmlns="{tei_ns}">{xml_string}</temp>'
        temp_node = ET.fromstring(temp_xml)
        if temp_node.text:
            if len(parent_element) > 0:
                parent_element[-1].tail = (parent_element[-1].tail or "") + temp_node.text
            else:
                parent_element.text = (parent_element.text or "") + temp_node.text
        for child in list(temp_node):
            parent_element.append(child)
    except Exception:
        parent_element.text = (parent_element.text or "") + xml_string

# --- CREAZIONE EDIZIONE CRITICA (SINGOLI FILE) ---

def crea_critica(filename, content):
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ET.register_namespace('', tei_ns)
    root = ET.Element(f"{{{tei_ns}}}TEI")
    
    header = ET.SubElement(root, f"{{{tei_ns}}}teiHeader")
    # ... (metadati)

    text_el = ET.SubElement(root, f"{{{tei_ns}}}text")
    body = ET.SubElement(text_el, f"{{{tei_ns}}}body")
    
    # 1. Identifichiamo dove sono le barre e creiamo una lista di tuple (testo, unisci_a_successiva)
    lines = content.split('\n')
    processed_data = []

    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            processed_data.append((None, False))
            continue
        if re.match(r'^\d+$', raw_line):
            continue

        # Verifichiamo se finisce con / o //
        unisci = False
        if raw_line.endswith("//"):
            unisci = True
            raw_line = raw_line[:-2].strip()
        elif raw_line.endswith("/"):
            unisci = True
            raw_line = raw_line[:-1].strip()
        
        # Trasformiamo i tag inline
        line_xml = process_inline_tags(raw_line)
        processed_data.append((line_xml, unisci))

    # 2. Ricostruzione XML con gestione spazi condizionale
    current_div = body
    current_p = None
    unisci_a_precedente = False # Flag per la riga corrente

    for xml_line, unisci_prossima in processed_data:
        if xml_line is None:
            current_p = None
            unisci_a_precedente = False
            continue

        plain_text = re.sub(r'<.*?>', '', xml_line).strip()
        if not plain_text: continue

        # Titoli SERMO
        if "SERMO" in plain_text.upper() and (plain_text.isupper() or len(re.findall(r'[A-Z]', plain_text)) > len(plain_text)/2):
            current_div = ET.SubElement(body, f"{{{tei_ns}}}div", {"type": "sermon"})
            head = ET.SubElement(current_div, f"{{{tei_ns}}}head")
            inject_xml_content(head, xml_line, tei_ns)
            current_p = None
            unisci_a_precedente = False
            continue

        if current_p is None:
            current_p = ET.SubElement(current_div, f"{{{tei_ns}}}p")

        # LOGICA SPAZIATURA
        # Se la riga precedente NON finiva con / o //, aggiungiamo uno spazio
        spazio = "" if unisci_a_precedente else " "
        
        # Se il paragrafo è vuoto (inizio paragrafo), non mettiamo mai lo spazio
        if not (current_p.text or len(current_p) > 0):
            spazio = ""

        if "|" in xml_line:
            parts = xml_line.split("|", 1)
            bibl = ET.SubElement(current_p, f"{{{tei_ns}}}bibl", {"type": "source"})
            inject_xml_content(bibl, parts[0].strip(), tei_ns)
            inject_xml_content(current_p, spazio + parts[1].strip(), tei_ns)
        else:
            inject_xml_content(current_p, spazio + xml_line, tei_ns)
        
        # Passiamo il testimone alla riga successiva
        unisci_a_precedente = unisci_prossima
                
    return root

# Le altre funzioni (crea_interpretativa, save_xml, main loop) rimangono identiche.
# --- FUNZIONI PRINCIPALI ---

def crea_interpretativa(filename, content):
    """ Ex crea_diplomatica: Focus sulla struttura fisica (lb, pb, span laterali) """
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ET.register_namespace('', tei_ns)
    root = ET.Element(f"{{{tei_ns}}}TEI")
    
    header = ET.SubElement(root, f"{{{tei_ns}}}teiHeader")
    file_desc = ET.SubElement(header, f"{{{tei_ns}}}fileDesc")
    title_stmt = ET.SubElement(file_desc, f"{{{tei_ns}}}titleStmt")
    ET.SubElement(title_stmt, f"{{{tei_ns}}}title").text = f"Edizione Interpretativa: {filename}"
    
    text_el = ET.SubElement(root, f"{{{tei_ns}}}text")
    body = ET.SubElement(text_el, f"{{{tei_ns}}}body")
    ab = ET.SubElement(body, f"{{{tei_ns}}}ab")
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    current_page, lb_counter, prev_break_type = 0, 1, None 

    for line in lines:
        if re.match(r'^\d+$', line):
            current_page = int(line)
            ET.SubElement(ab, f"{{{tei_ns}}}pb", {"n": str(current_page), "xml:id": f"p{current_page}", "facs": f"{current_page}.jpg"})
            continue

        lb_attrs = {"n": str(lb_counter)}
        if prev_break_type == "/": lb_attrs["break"] = "no"
        elif prev_break_type == "//": lb_attrs["break"] = "no"; lb_attrs["rend"] = "="
        
        ET.SubElement(ab, f"{{{tei_ns}}}lb", lb_attrs)
        lb_counter += 1

        clean_line = line
        if "|" in line:
            parts = line.split("|", 1)
            side = "left" if current_page % 2 == 0 else "right"
            margin_xml = process_inline_tags(parts[0].strip())
            span_margin = ET.SubElement(ab, f"{{{tei_ns}}}span", {"type": f"sermo-bibl-{side}"})
            inject_xml_content(span_margin, margin_xml, tei_ns)
            clean_line = parts[1].strip()

        # --- MODIFICA SILLABAZIONE ---
        if clean_line.endswith("//"):
            prev_break_type = "//"
            # Sostituiamo // con il carattere ₌ a fine riga
            text_content = clean_line[:-2].strip() + "₌"
        elif clean_line.endswith("/"):
            prev_break_type = "/"
            # Se preferisci mantenere / o sostituire anche questo, puoi farlo qui
            text_content = clean_line[:-1].strip() + "-" 
        else:
            prev_break_type = None
            text_content = clean_line.strip()

        line_xml = process_inline_tags(text_content)
        inject_xml_content(ab, line_xml, tei_ns)

    return root


def save_xml(root, filepath):
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

# Main loop
os.makedirs("output_interpretativa", exist_ok=True)
os.makedirs("output_critica", exist_ok=True)

for fn in os.listdir("./testi_txt"):
    if fn.endswith(".txt"):
        with open(f"testi_txt/{fn}", "r", encoding="utf-8") as f:
            raw_text = f.read()
            save_xml(crea_interpretativa(fn, raw_text), f"output_interpretativa/{fn.replace('.txt', '.xml')}")
            save_xml(crea_critica(fn, raw_text), f"output_critica/{fn.replace('.txt', '.xml')}")

print("Finito! Le parole greche sono ora marcate con xml:lang='grc'.")