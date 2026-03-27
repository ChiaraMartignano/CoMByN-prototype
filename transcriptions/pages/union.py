import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

def merge_tei_files(input_folder, output_filename, edition_title, is_critica=False):
    tei_ns = "http://www.tei-c.org/ns/1.0"
    xml_ns = "http://www.w3.org/XML/1998/namespace" # Namespace per xml:id
    ET.register_namespace('', tei_ns)
    ET.register_namespace('xml', xml_ns)
    
    # 1. Creiamo la struttura radice del nuovo file unico
    root = ET.Element(f"{{{tei_ns}}}TEI")
    header = ET.SubElement(root, f"{{{tei_ns}}}teiHeader")
    file_desc = ET.SubElement(header, f"{{{tei_ns}}}fileDesc")
    title_stmt = ET.SubElement(file_desc, f"{{{tei_ns}}}titleStmt")
    ET.SubElement(title_stmt, f"{{{tei_ns}}}title").text = edition_title
    
    # Metadati minimi per la pubblicazione
    pub_stmt = ET.SubElement(file_desc, f"{{{tei_ns}}}publicationStmt")
    ET.SubElement(pub_stmt, f"{{{tei_ns}}}p").text = "Edizione integrale unificata"
    source_desc = ET.SubElement(file_desc, f"{{{tei_ns}}}sourceDesc")
    ET.SubElement(source_desc, f"{{{tei_ns}}}p").text = "Unione di file XML/TEI sorgente"

    text_el = ET.SubElement(root, f"{{{tei_ns}}}text")
    body_root = ET.SubElement(text_el, f"{{{tei_ns}}}body")

    # 2. Otteniamo la lista dei file ordinati
    files = sorted([f for f in os.listdir(input_folder) if f.endswith('.xml')])
    
    if not files:
        print(f"Nessun file trovato in {input_folder}")
        return

    print(f"Unendo {len(files)} file da {input_folder}...")

    # 3. Iteriamo sui file ed estraiamo il contenuto di <body>
    for filename in files:
        file_path = os.path.join(input_folder, filename)
        try:
            tree = ET.parse(file_path)
            file_root = tree.getroot()
            file_body = file_root.find(f".//{{{tei_ns}}}body")
            
            if file_body is not None:
                body_root.append(ET.Comment(f" Inizio file: {filename} "))
                for child in list(file_body):
                    body_root.append(child)
                    
        except Exception as e:
            print(f"Errore durante la lettura di {filename}: {e}")

    # 4. LOGICA DI NUMERAZIONE (Solo per l'edizione critica)
    if is_critica:
        div_counter = 1
        # Cerchiamo tutti i div nel corpo unificato
        for div in body_root.findall(f".//{{{tei_ns}}}div[@type='chapter']"):
            # Assegnazione attributi alla div
            div.set("n", str(div_counter))
            div.set(f"{{{xml_ns}}}id", f"chap{div_counter}")
            
            # Numerazione paragrafi all'interno di questa div
            p_counter = 1
            for p in div.findall(f".//{{{tei_ns}}}p"):
                p.set(f"{{{xml_ns}}}id", f"chap{div_counter}p{p_counter}")
                p_counter += 1
            
            div_counter += 1

    # 5. Salvataggio finale
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"File unificato creato: {output_filename}")

# --- ESECUZIONE ---

folder_interp = "output_interpretativa"
folder_crit = "output_critica"

# Creazione dell'edizione unificata Interpretativa (senza numerazione extra)
merge_tei_files(
    folder_interp, 
    "Edizione_Interpretativa_Completa.xml", 
    "Edizione Interpretativa Unificata",
    is_critica=False
)

# Creazione dell'edizione unificata Critica (con numerazione div e p)
merge_tei_files(
    folder_crit, 
    "Edizione_Critica_Completa.xml", 
    "Edizione Critica Unificata",
    is_critica=True
)