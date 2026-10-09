# fatturatore

CLI minimale per generare una fattura elettronica XML in formato FatturaPA `FPR12` per un cliente preconfigurato.

## Installazione

Richiede Python 3.11 o successivo e non ha dipendenze esterne. Dalla root del repository:

```bash
python3 -m pip install -e .
```

Dopo l'installazione è disponibile il comando `fatturatore`. In alternativa si può eseguire il modulo senza installarlo:

```bash
python3 -m fatturatore
```

## Uso

La modalità predefinita è interattiva:

```bash
fatturatore
```

All'avvio mostra il banner `FATTURATORE`, chiede il lordo senza bollo e propone la data odierna. È possibile confermare oggi oppure inserire una data diversa in formato `GG/MM/AAAA` o `AAAA-MM-GG`. Prima della creazione presenta tutti i dati in un riepilogo e richiede una conferma esplicita. Per l'uso non interattivo è possibile passare direttamente il lordo:

Durante l'inserimento sono disponibili il normale editing da terminale, i tasti freccia e la cronologia dei valori digitati nella sessione corrente.

```bash
fatturatore 2917
```

Colori e simboli sono abilitati automaticamente nei terminali compatibili. Per disabilitarli:

```bash
NO_COLOR=1 fatturatore
```

Sono accettati sia `2917.00` sia il formato italiano `2.917,00`. Il file viene scritto nella cartella `Downloads` dell'utente con il nome previsto per l'invio a SdI, per esempio:

```text
~/Downloads/ITCODICEFISCALE_00001.xml
```

Il lordo inserito è considerato comprensivo di:

- compenso per consulenza;
- rivalsa INPS del 4%;

Il bollo virtuale da 2,00 EUR non deve essere incluso: viene aggiunto automaticamente al totale del documento.

Per esempio, `2917` genera un compenso di 2.804,81 EUR e una rivalsa INPS di 112,19 EUR; aggiungendo il bollo, il totale del documento diventa 2.919,00 EUR.

Data, numero fattura e progressivo di invio sono automatici. I progressivi vengono conservati nel file locale `.fatturatore-state.json`. Al primo utilizzo reale è importante allineare il numero fattura con l'ultima fattura già emessa:

```bash
fatturatore 2917 --numero 12
```

Il comando successivo userà automaticamente `13`. Per specificare una data diversa o una cartella di destinazione:

```bash
fatturatore 2917 --data 2026-10-07 --output ./fatture
```

Per visualizzare o modificare facilmente il prossimo numero fattura:

```bash
fatturatore -p
```

La forma estesa equivalente è `fatturatore --progressivi`. Il gestore consente di impostare il prossimo numero fattura o selezionare un anno diverso. Le modifiche vengono salvate nel file locale `.fatturatore-state.json` senza generare fatture. Il progressivo tecnico di invio viene gestito automaticamente dalla CLI e non richiede interventi manuali.

## Dati incorporati

I dati fiscali reali sono conservati esclusivamente in `fatturatore.local.json`, che è ignorato da Git. Il file tracciabile `fatturatore.example.json` contiene solo segnaposto anonimi. Per una nuova installazione:

```bash
cp fatturatore.example.json fatturatore.local.json
chmod 600 fatturatore.local.json
```

La configurazione locale contiene i dati del cedente e del cliente, oltre a:

- regime fiscale `RF19` (forfettario);
- natura IVA `N2.2`;
- cassa previdenziale `TC22` (INPS), aliquota 4%;
- bollo virtuale da 2,00 EUR;
- le due causali indicate;
- descrizione della prestazione: `Consulenza`.

Non sono presenti dati di pagamento perché non sono stati forniti; il relativo blocco è facoltativo nel tracciato FatturaPA.

L'XML dichiara la codifica UTF-8 e rappresenta i caratteri non ASCII con riferimenti numerici (per esempio `è` come `&#232;`). Il testo resta invariato e gli accenti sono preservati anche se il file viene letto con una codifica diversa durante l'importazione.

## Verifica

Eseguire i test con:

```bash
python3 -m unittest discover -s tests -v
```

La CLI genera XML ben formato secondo il tracciato FatturaPA ordinario. Prima dell'invio reale è comunque consigliato usare il controllo disponibile nel portale Fatture e Corrispettivi: SdI applica anche controlli fiscali e anagrafici che non fanno parte del solo schema XSD.
