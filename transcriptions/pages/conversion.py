import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- FUNZIONI DI SUPPORTO ---

def process_inline_tags(text):
    # Protegge i caratteri XML riservati
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 1. Greco
    text = re.sub(r'([\u0370-\u03ff]+(?:[\s,.;:][\u0370-\u03ff]+)*)', 
                  r'<span xml:lang="grc">\1</span>', text)
    
    # 2. Corsivo
    text = re.sub(r'_(.*?)_', r'<hi rend="italic">\1</hi>', text)
    
    # 3. Allineamenti
    text = re.sub(r'\[c\](.*?)\[/c\]', r'<span rend="align-center">\1</span>', text)

    # 4. Spostamenti (Float Above/Under)
    # Trasformiamo i marcatori in tag XML che inject_xml_content riconoscerà
    text = re.sub(r'\[u\](.*?)\[/u\]', r'<span type="float-under">\1</span>', text)
    text = re.sub(r'\[a\](.*?)\[/a\]', r'<span type="float-above">\1</span>', text)
    
    return text
    
    return text

def inject_xml_content(parent_element, xml_string, tei_ns):
    """ Converte stringa XML in nodi e li appende. """
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
    except Exception as e:
        parent_element.text = (parent_element.text or "") + xml_string

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

def crea_critica(filename, content):
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ET.register_namespace('', tei_ns)
    root = ET.Element(f"{{{tei_ns}}}TEI")
    
    # ... (Header standard) ...
    header = ET.SubElement(root, f"{{{tei_ns}}}teiHeader")
    # ...

    text_el = ET.SubElement(root, f"{{{tei_ns}}}text")
    body = ET.SubElement(text_el, f"{{{tei_ns}}}body")
    
    # Unione parole spezzate
    content = content.replace("//\n", "").replace("/\n", "")
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # --- FASE 1: LOGICA DI SPOSTAMENTO DELLE STRINGHE ---
    buffer_lines = []
    pending_above = [] # Codice XML da aggiungere alla riga successiva

    for line in lines:
        if re.match(r'^\d+$', line): continue
        
        # Processiamo i tag inline (inclusi [u] e [a] che diventano <span>)
        processed_line = process_inline_tags(line)
        
        # Estraiamo i tag float-under per mandarli sopra
        under_fragments = re.findall(r'<span type="float-under">.*?</span>', processed_line)
        for frag in under_fragments:
            if buffer_lines:
                buffer_lines[-1] += " " + frag # Sposta alla fine della precedente
            processed_line = processed_line.replace(frag, "")

        # Estraiamo i tag float-above per mandarli sotto
        above_fragments = re.findall(r'<span type="float-above">.*?</span>', processed_line)
        for frag in above_fragments:
            pending_above.append(frag)
            processed_line = processed_line.replace(frag, "")

        # Se c'erano frammenti in attesa dalla riga precedente, li aggiungiamo qui
        if pending_above:
            processed_line += " " + " ".join(pending_above)
            pending_above = []
            
        buffer_lines.append(processed_line)

    # --- FASE 2: COSTRUZIONE EFFETTIVA DELL'ALBERO XML ---
    current_div = body
    current_p = None
    
    for xml_line in buffer_lines:
        # Controllo se la riga (senza tag) è un titolo SERMO
        plain_text = re.sub(r'<.*?>', '', xml_line).strip()
        if not plain_text: continue

        if "SERMO" in plain_text.upper() and (plain_text.isupper() or len(re.findall(r'[A-Z]', plain_text)) > len(plain_text)/2):
            current_div = ET.SubElement(body, f"{{{tei_ns}}}div", {"type": "sermon"})
            head = ET.SubElement(current_div, f"{{{tei_ns}}}head")
            inject_xml_content(head, xml_line, tei_ns)
            current_p = None
            continue

        # Gestione margine e paragrafi
        if "|" in xml_line:
            current_p = ET.SubElement(current_div, f"{{{tei_ns}}}p")
            parts = xml_line.split("|", 1)
            bibl = ET.SubElement(current_p, f"{{{tei_ns}}}bibl", {"type": "source"})
            inject_xml_content(bibl, parts[0].strip(), tei_ns)
            inject_xml_content(current_p, parts[1].strip(), tei_ns)
        else:
            if current_p is None:
                current_p = ET.SubElement(current_div, f"{{{tei_ns}}}p")
            inject_xml_content(current_p, xml_line, tei_ns)
                
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