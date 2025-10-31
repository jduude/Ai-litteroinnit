# Ai-litteroinnit

Ai avusteisten litterointien hallintasovellus.
Esimerkiksi ms word:in tekemät litteroinnit äänitiedostosta.

## Sovelluksen toiminnot

* Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
* Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan litterointeja.
* Litteroinnin tiedot koostuu alkuperäisen ääntiedoston tiedostonimestä, äänitiedoston pituudesta, äänitteen päivämäärästä, tiedoston sisällön otsikosta sekä litteroidusta tekstistä aikakoodeineen
* käyttäjä voi muokata ja korjata automaattisen litteroinnin tekstejä
* Käyttäjä näkee sovellukseen lisätyt litteroinnit.
* Käyttäjä pystyy etsimään litteroitujen tekstien sisältöjä, äänitiedoston nimiä, otsikoita hakusanalla.
* Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät litteroinnit.
* Käyttäjä pystyy valitsemaan litteroinnille yhden tai useamman luokittelun (litteroinnin kieli, äänitiedoston sisällön genre (esim luento).


## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```
