Text Line Changer v2.2
======================

Een tool om teksten met een instelbaar interval naar een tekstbestand
te schrijven — handig als OBS-tekstbron voor streams.


VEREISTEN
---------
- Windows 10 of 11
- Python 3.10 of nieuwer (https://www.python.org/downloads/)
  Let op: vink "Add Python to PATH" aan tijdens de installatie!


DIRECT STARTEN (zonder bouwen)
-------------------------------
Dubbelklik op:  text_line_changer.py

Of via de opdrachtprompt:
  python text_line_changer.py


EXE BOUWEN
----------
Dubbelklik op:  build.bat

Na het bouwen staat de EXE in:  dist\TextLineChanger.exe

Die EXE kun je overal naartoe verplaatsen en starten zonder
dat Python geïnstalleerd hoeft te zijn.


GEBRUIK
-------
1. Kies een uitvoerbestand (bijv. C:\OBS\tekst.txt)
2. Voeg teksten toe via "+ Toevoegen"
3. Bewerk de tekst in het tekstvak (Enter = nieuwe regel in uitvoer)
4. Klik "Opslaan" om op te slaan
5. Schakel items in/uit via ☑/☐
6. Stel het interval in (seconden)
7. Druk op START

Wijs in OBS een "Tekst (GDI+)"-bron aan op het uitvoerbestand.
De tekst wordt dan automatisch bijgewerkt.


INSTELLINGEN
------------
Alle instellingen worden automatisch opgeslagen in:
  C:\Users\<gebruiker>\.text_line_changer.json

Bij het volgende opstarten worden je teksten en instellingen
automatisch herladen.


SNELTOETSEN
-----------
Geen — alles werkt via de knoppen in de interface.
