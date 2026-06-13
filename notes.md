09/04/2026

Als een ToM0 optimistisch speelt, moet ToM1 pessimistisch spelen. 

Wat is ToM1's threshold voor ToM0 om te gaan toepen? (Bij welke geloof van opponent hand strength (/n) zal hij toepen omdat hij denkt te winnen OF omdat hij denkt dat de tegenstander niet meegaat (bluffen))

Bij een optimistiche is het beter om later te toepen omdat je kan bluffen
Bij een pessimistische kan dat niet

In observe_play bouw je een bayesian prob distribution over wat de tegenstander kan hebben, gebaseerd op de strategie van de tegenstander (stel een optimistische gooit een harten 8 op, dan schakel je de harten 9 en 10 uit) en op de hand van jezelf. 


hand_strength_opp = sum(strength(K) * P(K)) voor K in Kaarten


Voor nu ToM1 optimaliseren tegen OptimisticZeroOrder


Stappenplan: 
1) zet alle kaarten op 1/28 kans dat de tegenstander deze heeft
2) Telkens wanneer er een kaart geobserveerd wordt bij de tegenstander, ga na welke kaarten de Opt ToM0 speler niet meer in zijn hand heeft gegeven wat je hebt gezien
3) Normaliseer deze kansen
4) Beslis of ToM1 gaat toepen, gebaseerd op de ToM1's geloof of de tegenstander een goede hand heeft (threshold)*
5) Als de ander meegaat, speel dan Rationeel. 

*: Dit was iets van 4 of 4.5
________________________________________________________________________________________________________________________________________________________________________
16/04/2026
________________________________________________________________________________________________________________________________________________________________________

22/04/2026
Voor: 
Verwijder de niet-geauthoreerde code, zorg dat een ToM1-speler de kaart speelt die wint van de hoogst waarschijnlijke in zijn opp hand distribution* 
*: Wat als meerdere kaarten dezelfde probability hebben? 
    - Kies dan de eerste in de rij?
        - Dit zou een ToM2 speler dan goed kunnen exploiten. 

Voor alle kaarten langsgaan moet hij uitrekenen wat de kans is om te winnen met deze kaart (Maak hier een functie voor), en speel deze kaart als hij hoger is dan een bepaalde threshold. (Misschien 50%?, maar kijk ook vooral naar andere waarden.)
Als geen kaart dit heeft, of bluffen of laagste kaart weggooien.

ToM2 doet monte carlo simulation, of daadwerkelijk alle mogelijke hands van de tegenstander modelen (28nCr4) en dan kijken wat een ToM1 zou doen in deze situatie, heeft vooral te maken met intepretative ToM. Hierbij zou je dan de simulation op maar 10 games oid zetten, omdat het erg computationeel duur is. 

Bronnen:
zoek een over ToM in bluff spellen 
    - of poker



04/05
Bij introductie zeggen dat ToM weinig nut heeft met toepen, en redeneren waarom monte carlo gebruiken 
Goed uitleggen de voordelen van Monte Carlo in het verminderen van simulaties met de distributies van ToM2 over geloven van ToM1, met referentie naar monte carlo simulaties in bayesien ToM agents van Joshua Tannenbaum (zoek op Tannenbaum, Theory of Mind, MonteCarlo), ook naar ToM bij poker kijken. 

11/05
Vragen voor toestemming gebruik illustraties voor ToM1-reasoning. 
Wat wordt met inhoudsopgave aan het eind vd intro bedoeld? 

"The remainder of this thesis is structured as follows: in section 2 we ... "
Omdat ToM geen voordeel bij Toepen biedt, meer focusen op Monte Carlo met ToM. Benadruk hoe je ToM schaalbaar kunt maken dmv MonteCarlo sampling. 


18/05
ToM figuren zijn nu erg klein, misschien verplaatsen naar Appendix? 
"Hier kun je verwijzen vaan het RPS paper om te onderbouwen waarom je specifieke ToM1 agents modelleert" Hoezo? 


In het midden wit bij 0.50 procent. 


TODO: 
Bij ToM1 sectie report: "Interpretative en Predictive" als subsections hebben om te differentieren. 
Misschien https://en.wikipedia.org/wiki/Monte_Carlo_tree_search gebruiken voor motivatie monte carlo rollouts
https://link.springer.com/article/10.1007/s10458-022-09558-6 Harmen Paper "Higher-order theory of mind is especially useful in unpredictable negotiations"
Limitations section
Results beter explained
Is het interpretative of interpretive? 
Maak de discussie concreter: "It is about whether Monte Carlo is a useful approximation for second-order ToM. So make the main answer explicit: Monte Carlo succeeds computationally, but the current implementation fails strategically because it evaluates single-card plays/current tricks instead of full-round outcomes."





Introduceer Monte Carlo sampling als nieuwe methode, in plaats van het alleen te gebruiken. 

Notes wat is veranderd: 
- Quotes van RPS met \lq en \rq gedaan
- ToM2 voorbeeld poker (dikgedrukt)
- "In addition, the small card set means a ToM1 agent's beliefs of the opponent's hand is strongly influenced by their own."

Vragen: 
- Stukje onder "or if they can't be beaten" kan ik niet lezen en snap ik niet. 
- Vragen of stukje "A ToM0 player may infer that their opponent does not have cards of a certain suit by observing that their opponent has failed to follow suit, and will eliminate the possibility of their opponent having these cards by altering their own belief set. \textbf{It is important to note that ToM0 updates their beliefs by observing which cards were played, not by reasoning about unobservable mental content.}" goed is zo. 
- Blz. 5 comments linksonder. 
- Hoe results nu gestructueerd is. Moeten de values voor mu en Tau ook bij de methods beschreven worden? 
- Voor de wiskunde, hoofdletter S? 
- Puntje in discussie nagaan, vragen wat Harmen er nu van vindt. . 



Algemeen: 
- Harmen zei dat er voorbeelden geveven waren voor bepaalde ToM agenten maar niet voor anderen, dit moet wel gefixt worden. Volgens mij was dit de uitleg dat bij ToM0 ze altijd meegingen, en deze uitleg er niet bij ToM1 en ToM2 waren. 



Meeting 08/06 (laatste)
- Laten checken, vragen welke beter is bij discussie. 
- Vragen hoe de results uit te breiden want ben eigenlijk vergeten hoe
- Low threshold = 0.20, high threshold = 0.80
- Low Toep margin = 2, high toep margin = 8
- Mix = 9 for Toep margin, Mid Toep Margin = 4, 5, 6, low margin = 1 high threshold = 0.90, low threshold = 0.10, mid threshold = 0.50
- High Threshold and high margin does not affect results much. 

"Manipulating mu found little to no effect in the winrate of the ToM2 agents. However, a lower value for tau led to a significantly higher performance for all ToM2 models. (Lower value leads to more Toepen). This is likely because the original Toep margin was too high to effectively take advantage of a good hand. With a lower value tau, the model calls Toep more often when it actually should, and thus benefits more from this strategic play. "

Benoemen dat eerste results het opmerkelijk is dat ToM2 vs ToM1 zo slecht is, ookal passen zijn aannames wel bij de tegenstander. 
Benoemen dat Fo Vs Optimistic de beste strategie is, voor future research kijken waarom dit zo dominant is. 
Beide matrices laten zien, benoemen dat risicovol spel voor ToM2 nut heeft (ook in abstract en discussie)


Amount of ToM2 Toepen with toep_margin = 1 == 302741
Amount of ToM2 Toepen with toep_margin = regular == 75639
TODO: mid win threshold w/ high toepmargin vergelijken met mid win threshold w/ mid toepmargin (al gedaan, kijk foto's)


Vragen presentatie:
- Waarom ToM2 niet gemodelleerd met de interne policy? Als in, als een ToM2 agent weet dat hij tegen een OToM1 speelt, die dus zijn interne opp card distribution updated met dat de tegenstander geen hogere kaarten heeft dan de gespeelde, hier gebruik van maakt?


Todo: 
- Capitalize Theory of Mind everywhere. 


































Learn more about professional AI Safety
Maybe land an internship