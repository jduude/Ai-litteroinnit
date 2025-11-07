# Ai-litteroinnit

Ai avusteisten litterointien hallintasovellus.
Esimerkiksi ms word:in tekemät litteroinnit äänitiedostosta.

## Sovelluksen toiminnot

* Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
* Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan litterointeja.
* Litteroinnin tiedot koostuu alkuperäisen ääntiedoston tiedostonimestä  (tai netti urlista), tiedoston sisällön otsikosta sekä litteroidusta tekstistä aikakoodeineen
* käyttäjä voi muokata ja korjata automaattisen litteroinnin tekstejä
* Käyttäjä näkee sovellukseen lisätyt litteroinnit.
* Käyttäjä pystyy etsimään litteroitujen tekstien sisältöjä

## TODO
* Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät litteroinnit.
* Käyttäjä pystyy valitsemaan litteroinnille yhden tai useamman luokittelun (litteroinnin kieli, äänitiedoston sisällön genre (esim luento).
* lisää metatietoja litterointiin: äänitiedoston pituudesta, äänitteen päivämäärästä, litteroinnin muokkauspäivämäärät
* tekstin muokkaus päivämäärä
* haku äänitiedoston nimellä ja otsikoista



## Sovelluksen asennus

Asenna `flask`kirjasto:

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


## Käyttöohjeet

Toimii tällä hetkellä Youtube automaattisilla tekstityksillä ja word:in transcribe toiminnolla. 

### Youtube  
kopioi teksti esim Chrome dev toolista.
Aktivoi tekstitykset:
![Youtube cc button](readme-images/2025-11-07_23-13-53-785_Dimmer.png)

ja kopioi dev toolin network ikkunasta json 
![Dev tools network response](readme-images/2025-11-07_23-14-12-754_Dimmer.png)

ja liitä Aikaleimattu teksti tekstikenttään.


### Word 

Kopioi transcribe toiminnon tulos aikaleimoilla

![Word transcribe]( 
readme-images/2025-11-07_22-58-13-275_Dimmer.png)

ja liitä Aikaleimattu teksti tekstikenttään.

![Word transcribe](readme-images/2025-11-07_23-05-18-775_Dimmer.png)
