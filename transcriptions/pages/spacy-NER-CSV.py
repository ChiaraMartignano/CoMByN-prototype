import spacy
from lxml import etree
import csv
import os

# 1. Caricamento del modello
print("Caricamento modello spaCy per il latino...")
nlp = spacy.load("la_core_web_lg")

# --- CONFIGURAZIONE ---
input_xml = '../../assets/data/gesner_critical.xml' 
output_csv = 'entita_da_revisionare.csv'
# ----------------------

def extract_entities_with_offsets(xml_path, csv_path):
    if not os.path.exists(xml_path):
        print(f"Errore: Il file {xml_path} non esiste.")
        return

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(xml_path, parser)
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # Recuperiamo il testo del body
    body = tree.find('.//tei:body', ns)
    if body is None: body = tree.getroot()
    
    # Creiamo la stringa di testo mantenendo la posizione
    full_text = "".join(body.itertext())
    doc = nlp(full_text)
    
    entities = []
    FOCUS_NAMES = {'alexander', 'darius', 'lycurgus', 'cyrus'}

    for token in doc:
        # Consideriamo i nomi propri o le entità riconosciute
        if token.pos_ == "PROPN" or token.ent_type_ or token.lemma_.lower() in FOCUS_NAMES:
            if len(token.text) < 3: continue
            
            label = token.ent_type_ if token.ent_type_ else "PER"
            lemma = token.lemma_.lower()
            
            # Correzione automatica etichette
            if label == "LOC" and (lemma in FOCUS_NAMES or token.text.endswith(('us', 'is', 'i', 'es'))):
                label = "PER"
            
            # Filtro parole comuni
            if token.text.upper() in ['IN', 'ET', 'SED', 'UT', 'NAM', 'QUOD', 'AD', 'SI', 'NON', 'CUM']:
                continue
            
            # Aggiungiamo le coordinate spaziali
            entities.append({
                'testo_trovato': token.text,
                'lemma': token.lemma_,
                'categoria_proposta': label,
                'inizio': token.idx,                # Indice del carattere iniziale
                'fine': token.idx + len(token.text)   # Indice del carattere finale
            })

    # Salvataggio nel CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['testo_trovato', 'lemma', 'categoria_proposta', 'inizio', 'fine']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entities)
    
    print(f"CSV generato con {len(entities)} occorrenze. File: {csv_path}")

extract_entities_with_offsets(input_xml, output_csv)