# RosettaCNC API Client - C++

## Stato del porting

Questa directory contiene il porting nativo C++14 di
`../python/cnc_api_client_core.py`, compatibile con il contratto API Server
v1.5.3.

Stato delle API pubbliche di protocollo:

- GET: 36/36 implementati, inclusi array, oggetti annidati e dati binari.
- SET: 31/32 implementati.
- CMD: 56/56 implementati.
- Convenience method threaded: 10/10 implementati.
- Gestione connessione TCP e TLS 1.2 tramite Schannel implementata.
- Proprietà della connessione e `connection_clone()` implementati.

L'unico SET non implementato è `set_kinematics()`: anche il riferimento Python
v1.5.3 è un segnaposto che restituisce `False` e non definisce alcun payload.

`connect_direct()` restituisce esplicitamente `false`. Il riferimento Python
delega questa modalità al modulo proprietario esterno `cnc_direct_access`, del
quale il repository non contiene né sorgenti né ABI C/C++. Non è quindi
possibile fornire un backend C++ equivalente senza tale dipendenza. La normale
connessione TCP/TLS non è interessata.

## Caratteristiche

- Socket TCP/IP con richieste e risposte delimitate da newline.
- TLS 1.2 Schannel con validazione automatica del certificato e del nome host.
- Serializzazione JSON con tipi corretti e escaping delle stringhe.
- Parsing JSON dependency-free per tutte le forme restituite dall'API v1.5.3,
  inclusi Unicode, oggetti annidati e array multidimensionali.
- Dati simulator/toolpath in formato binario e decodifica Base64.
- Operazioni `force_sync` e wrapper asincroni con callback.
- Strutture con puntatori opzionali rese non copiabili per evitare double-free.

## File

- `cnc_api_client_core.h`: dichiarazioni, costanti e strutture dati.
- `cnc_api_client_core.cpp`: implementazione del client.
- `main.cpp`: esempio e chiamate dimostrative.
- `CncAPIClient.vcxproj`: progetto Visual Studio 2019.

## Compilazione

Requisiti:

- Windows 10 o successivo.
- Visual Studio 2019 o successivo.
- Platform Toolset v142.

```powershell
msbuild CncAPIClient.vcxproj /p:Configuration=Debug /p:Platform=x64 /t:Build
```

## Verifica

La build Debug x64 è verificata con warning level 3. Le richieste e i parser
complessi sono verificati anche mediante un server TCP mock locale, comprese la
correttezza dei tipi JSON numerici, le sequenze Unicode, gli utensili completi,
gli ordini di lavoro, i punti programmati e le descrizioni dei parametri CNC.

La verifica TLS contro un server RosettaCNC reale e la validazione funzionale su
macchina richiedono l'ambiente di destinazione e non possono essere eseguite dal
solo repository.

## Licenza

Porting C++ del client RosettaCNC Python v1.5.3.
