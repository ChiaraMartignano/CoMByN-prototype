import csv
from lxml import etree

def extract_greek_words(xml_file, output_csv):
    # Definiamo il namespace TEI presente nel tuo file
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Errore nel caricamento del file: {e}")
        return

    data = []
    current_page = "N/D"
    current_line = "N/D"

    # Iteriamo su tutti gli elementi del corpo del testo
    # Usiamo descendent::* per mantenere l'ordine logico di apparizione
    for elem in root.xpath('//tei:text//*', namespaces=ns):
        
        # Se incontriamo un break di pagina, aggiorniamo il numero
        if elem.tag == f"{{{ns['tei']}}}pb":
            current_page = elem.get('n', 'N/D')
            
        # Se incontriamo un break di riga, aggiorniamo il numero
        elif elem.tag == f"{{{ns['tei']}}}lb":
            current_line = elem.get('n', 'N/D')
            
        # Se incontriamo il nostro target <w xml:lang="grc">
        elif elem.tag == f"{{{ns['tei']}}}w" and elem.get('{http://www.w3.org/XML/1998/namespace}lang') == 'grc':
            word_text = "".join(elem.itertext()).strip()
            if word_text:
                data.append([word_text, current_page, current_line])

    # Scrittura del file CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['testo trascritto in automatico', 'numero pagina', 'numero verso'])
        writer.writerows(data)

    print(f"Estrazione completata! Trovate {len(data)} parole. File salvato in: {output_csv}")

# Esegui lo script
extract_greek_words('../../assets/data/gesner_interpretative.xml', 'parole_greche.csv')