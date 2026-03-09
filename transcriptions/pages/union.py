import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

def merge_tei_files(input_folder, output_filename, edition_title):
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ET.register_namespace('', tei_ns)
    
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

    # 2. Otteniamo la lista dei file e li ordiniamo alfabeticamente/numericamente
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
            
            # Cerchiamo il body del file singolo
            file_body = file_root.find(f".//{{{tei_ns}}}body")
            
            if file_body is not None:
                # Aggiungiamo un commento XML per separare le sorgenti (utile per debug)
                body_root.append(ET.Comment(f" Inizio file: {filename} "))
                
                # Appendiamo tutti i figli del body (ab, div, p, pb, ecc.)
                for child in list(file_body):
                    body_root.append(child)
                    
        except Exception as e:
            print(f"Errore durante la lettura di {filename}: {e}")

    # 4. Salvataggio finale
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    print(f"File unificato creato: {output_filename}")

# --- ESECUZIONE ---

# Percorsi delle cartelle create dallo script precedente
folder_interp = "output_interpretativa"
folder_crit = "output_critica"

# Creazione dell'edizione unificata Interpretativa
merge_tei_files(
    folder_interp, 
    "Edizione_Interpretativa_Completa.xml", 
    "Edizione Interpretativa Unificata"
)

# Creazione dell'edizione unificata Critica
merge_tei_files(
    folder_crit, 
    "Edizione_Critica_Completa.xml", 
    "Edizione Critica Unificata"
)