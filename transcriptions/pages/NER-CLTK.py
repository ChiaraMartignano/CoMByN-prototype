import os
import csv
from cltk import NLP

# 1. Inizializzazione per v2.5.1
# In questa versione è preferibile passare solo il codice lingua
print("Inizializzazione pipeline CLTK 2.5.1...")
try:
    # La pipeline standard include già POS e Lemmatizzazione
    cltk_nlp = NLP(language="lat") 
except TypeError:
    cltk_nlp = NLP("lat")

input_folder = 'testi_txt'
output_file = 'entita_estratte.csv'
risultati = []

# Lista di parole comuni da escludere (stop words latine tipiche a inizio frase)
STOP_WORDS_LAT = {'In', 'Et', 'Sed', 'Cum', 'Ut', 'Nam', 'Quod', 'Ad', 'Ab', 'Ex', 'At', 'Si', 'Quia'}

if not os.path.exists(input_folder):
    print(f"Errore: La cartella '{input_folder}' non esiste.")
else:
    for filename in os.listdir(input_folder):
        if filename.endswith(".txt"):
            print(f"Analisi di: {filename}...")
            
            with open(os.path.join(input_folder, filename), 'r', encoding='utf-8') as f:
                content = f.read()

            # Processamento
            doc = cltk_nlp.analyze(text=content)

            for word in doc.words:
                # In 2.5.1 usiamo word.upos (Universal Part of Speech)
                # I nomi propri sono solitamente 'PROPN'
                pos_tag = str(word.upos) if hasattr(word, 'upos') else ""
                
                # Controllo maiuscola
                text_val = word.string
                starts_upper = text_val[0].isupper() if text_val else False

                # LOGICA DI ESTRAZIONE:
                # Cattura se è marcato come nome proprio OPPURE se inizia con maiuscola ed è un sostantivo
                if pos_tag == 'PROPN' or (starts_upper and pos_tag == 'NOUN'):
                    
                    # Filtro stop words
                    if text_val in STOP_WORDS_LAT:
                        continue
                    
                    risultati.append({
                        'file': filename,
                        'forma_testo': text_val,
                        'lemma': word.lemma if word.lemma else text_val,
                        'pos_universale': pos_tag
                    })

# 3. Scrittura dei risultati
keys = ['file', 'forma_testo', 'lemma', 'pos_universale']
with open(output_file, 'w', newline='', encoding='utf-8') as output:
    dict_writer = csv.DictWriter(output, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows(risultati)

print(f"\nAnalisi completata!")
print(f"Entità trovate: {len(risultati)}")
print(f"File salvato: {os.path.abspath(output_file)}")