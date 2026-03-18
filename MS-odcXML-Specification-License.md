## Qu'est-ce que c'est ?

La **MS-odcXML-Specification-License** est une licence de spécification permissive que Microsoft a intégrée directement dans ses fichiers de définition de schémas XML (XSD) pour Office. Elle accorde la permission de copier, afficher et distribuer le contenu de la spécification, sur tout support et pour tout usage, sans frais ni redevance, à condition d'inclure l'avis de copyright de Microsoft sur toutes les copies.

Le nom provient de l'URL qu'elle référençait à l'origine sur MSDN : `http://msdn.microsoft.com/library/en-us/odcXMLRef/html/odcXMLRefLegalNotice.asp` — où "odc" signifie **Office Developer Center** et "XMLRef" désigne **XML Reference**.

## Pourquoi apparaît-elle dans `poi-ooxml-lite` ?

`poi-ooxml-lite` contient des classes générées à partir des schémas XSD de Microsoft, couvrant uniquement les parties les plus couramment utilisées du format Office Open XML. C'est une version sensiblement plus légère du jar complet `poi-ooxml-full`, et c'est une dépendance obligatoire de `poi-ooxml`.

Étant donné qu'Apache POI compile les schémas XSD originaux de Microsoft (via Apache XMLBeans) en classes Java, la licence embarquée dans ces fichiers XSD se propage en tant que licence de sous-composant. Le fichier LICENSE de POI précise explicitement qu'il inclut des sous-composants avec des avis de copyright et des conditions de licence distincts.

## Que permet et que restreint concrètement cette licence ?

En pratique, elle est assez permissive :

**Autorise :** la copie, l'affichage et la distribution du contenu de la spécification, librement et sans redevance. Une licence de brevet distincte a également été mise à disposition par Microsoft pour les implémentations du format XML.

**Exige :** l'inclusion de l'avis de copyright de Microsoft sur toute copie ou portion redistribuée.

**Exclut toute garantie :** Microsoft fournit la spécification « EN L'ÉTAT » (AS IS), sans aucune garantie expresse ou implicite — ni de qualité marchande, ni d'adéquation à un usage particulier, ni de non-contrefaçon, ni que les implémentations ne porteront pas atteinte aux droits de tiers.

**Interdit :** l'utilisation du nom et des marques de Microsoft dans toute publicité relative à la spécification sans autorisation écrite préalable.

## En complément — l'angle ECMA-376

Les définitions de schémas Office Open XML utilisées par Apache POI font partie de la norme ECMA-376, et conformément à l'article 9.4 des statuts de l'ECMA, tous les documents approuvés sont mis à disposition de toutes les parties intéressées sans restriction. De plus, Microsoft et Adobe ont tous deux accordé des licences de brevet sur ces travaux.

## En résumé pour ton projet

D'un point de vue conformité, il s'agit d'une licence de spécification permissive et à faible risque. Ce n'est pas une licence copyleft et elle n'impose aucune obligation de redistribution sur ton propre code. La principale obligation est de conserver l'avis de copyright si tu redistribues les fichiers de schémas eux-mêmes. Combinée à la standardisation ECMA-376 et à l'Open Specification Promise de Microsoft, l'utilisation de `poi-ooxml-lite` dans un contexte commercial ou bancaire (comme chez BNP Paribas) est une pratique courante et juridiquement bien établie.
