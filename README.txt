Sindaci d'Italia
Elia Perantoni VR429673

Lo script utilizza i codici ISTAT dei comuni italiani presenti nel file abitanti_2019_2020.csv (fornito a lezione) per
effettuare una serie di richieste HTTP (al sito comuni-italiani.it) e compilare una lista di sindaci che viene scritta
sul file output.csv.

Vengono utilizzate le funzionalità asincrone di Python 3 (normalmente conosciute come coroutine). In sostanza funziona
così: le funzioni possono essere marcate 'async'. Quando una funzione è 'async', questa può volontariamente sospendersi
e permettere ad un'altra funzione 'async' di proseguire la propria esecuzione.
Se, ad esempio, una funzione effettua una richiesta HTTP, mentre aspetta il risultato dal server potrebbe permettere a
qualche altra funzione di fare del lavoro utile.
In questo modo si riduce notevolmente il tempo richiesto per reperire tutti i sindaci.

Le funzioni asincrone utilizzate sono: un reader, diversi fetcher e un writer. Il reader legge i codici ISTAT dal file
abitanti_2019_2020.csv e li mette in una coda chiamata 'in'. I fetcher leggono i codici ISTAT da questa coda e fanno
le richieste HTTP al sito comuni-italiani.it per reperire il nome del sindaco. Quando il server risponde, la tupla
(codice_istat, sindaco) viene inserita in una coda chiamata 'out'. Il writer è in attesa di tuple su questa coda. Quando
ne riceve una, la scrive sul file 'output.csv'.

Il progresso dello script è monitorabile da terminale con una barra di progresso. Eventuali errori vengono segnalati
sempre su terminale.

All'avvio, lo script leggerà il file output.csv e ignorerà i comuni già presenti.

Esempio di esecuzione:

$ virtualenv venv
$ source venv/bin/activate
$ (venv) pip install -r requirements.txt
$ (venv) python main.py
