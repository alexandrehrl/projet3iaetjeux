# LU3IN025 – Rapport TME 1 à 3
## Affectation stable par l'algorithme de Gale-Shapley

---

## 1. Reformulation du sujet

On cherche à affecter **n = 13 étudiants** dans **m = 10 parcours** du Master Informatique de Sorbonne Université (AI2D, BIM, CCA, IMA, MIND, QI, RES, SAR, SESI, STL) en tenant compte des préférences des deux côtés. Chaque parcours possède une capacité d'accueil (capacités : [2,1,1,1,2,1,1,1,1,2], somme = 13). L'objectif est de produire des affectations stables via l'algorithme de Gale-Shapley, d'analyser leurs performances, puis d'optimiser l'équité via la Programmation Linéaire en Nombres Entiers (PLNE) avec Gurobi.

---

## 2. Structures de données et description du code

### 2.1 Fichier principal : `projet.py`

Le code est organisé en **six classes** :

| Classe | Rôle |
|---|---|
| `PreferenceData` | Lecture des fichiers, stockage de CE, CP, matrices de rang |
| `GaleShapleyStudentSide` | GS côté étudiants (Q2–Q3) |
| `GaleShapleySpeSide` | GS côté parcours (Q4) |
| `StabilityChecker` | Détection des paires instables (Q6) |
| `RandomGenerator` | Génération d'instances aléatoires (Q7) |
| `PerformanceMeasurer` | Mesures et tracé des courbes (Q8–Q10) |
| `PLNESolver` | Formulations PLNE avec Gurobi (Q11–Q14) |

### 2.2 Matrices principales (Q1)

- **CE[i]** : liste ordonnée des IDs de parcours selon les préférences de l'étudiant i (1er choix en tête). Exemple : `CE[0] = [5, 9, 7, 6, 8, 3, 2, 0, 1, 4]` → Etu0 préfère QI en premier.
- **CP[j]** : liste ordonnée des IDs d'étudiants selon les préférences du parcours j. Exemple : `CP[0] = [7, 9, 11, 5, …]` → AI2D préfère Etu7 en premier.
- **rank\_etu[i][j]** : rang du parcours j dans la liste de l'étudiant i (0 = meilleur). Précalculé en O(n×m).
- **rank\_spe[j][i]** : rang de l'étudiant i dans la liste du parcours j (0 = meilleur). Précalculé en O(n×m).

---

## 3. Réponses aux questions

### Q2 – Structures de données pour GS côté étudiants

Pour rendre les cinq opérations efficaces :

| Opération | Structure | Complexité |
|---|---|---|
| 1. Trouver un étudiant libre | `deque` de libres | O(1) |
| 2. Prochain parcours à proposer | `next_proposal[i]` (liste) | O(1) |
| 3. Rang de l'étudiant i dans le parcours j | `rank_spe[j][i]` (tableau 2D pré-calculé) | O(1) |
| 4. Étudiant le moins préféré du parcours j | `worst_heap[j]` : **max-heap** sur rank_spe | O(log cap_j) |
| 5. Remplacer un étudiant | `assignment[j]` (set) + `heapreplace` | O(log cap_j) |

La max-heap stocke `(-rank_spe[j][i], i)` pour que le minimum Python (sommet) corresponde à l'étudiant le **pire** du parcours j (rang le plus élevé).

**Occupation mémoire** : O(n×m) pour les matrices de rang, O(n) pour les structures auxiliaires.

---

### Q3 – GS côté étudiants : algorithme et complexité

**Algorithme :**
1. Tous les étudiants sont libres ; `next_proposal[i] = 0` pour tout i.
2. Tant qu'il existe un étudiant libre i :
   - j = `CE[i][next_proposal[i]]` ; incrémenter `next_proposal[i]`.
   - Si `|assignment[j]| < cap_j` : affecter i à j.
   - Sinon : soit w le pire de assignment[j] (sommet du heap).
     - Si `rank_spe[j][i] < rank_spe[j][w]` : remplacer w par i (w redevient libre).
     - Sinon : i reste libre et proposera au suivant.

**Complexité :**
- Chaque étudiant propose au plus m fois → au plus n×m propositions.
- Chaque proposition : O(log cap_j) pour les opérations de heap.
- **Total : O(n × m × log(cap_max))**. Avec des capacités équilibrées (cap ≈ n/m) : O(n × m × log(n/m)).

Sur l'instance : **28 propositions** suffisent (bien inférieur à n×m = 130).

---

### Q4 – GS côté parcours : adaptation et complexité

**Adaptation :** Les parcours jouent le rôle des « hôpitaux qui proposent ». Un parcours j est *actif* tant qu'il n'a pas atteint sa capacité et qu'il a des étudiants à contacter. Quand un étudiant i reçoit une proposition de j alors qu'il est déjà affecté à j', il choisit le meilleur selon ses préférences et j' peut redevenir actif.

**Structures (Q4) :**

| Opération | Structure | Complexité |
|---|---|---|
| Parcours actif | `active` (set) | O(1) |
| Prochain étudiant à contacter | `next_proposal[j]` (liste) | O(1) |
| Comparer deux parcours pour l'étudiant i | `rank_etu[i][j]` (tableau 2D) | O(1) |
| Parcours actuel de l'étudiant i | `current_spe[i]` (liste) | O(1) |
| Modifier l'affectation | `assignment[j]` (set) | O(1) |

**Complexité :** Chaque parcours propose au plus n fois → au plus m×n propositions, chacune en O(1). **Total : O(n × m)** — strictement meilleure que le côté étudiant si cap est grand.

Sur l'instance : **57 propositions**.

---

### Q5 – Application sur les fichiers de test

Les deux algorithmes produisent la **même affectation** (unique affectation stable) :

| Parcours | Capacité | Étudiants affectés |
|---|---|---|
| AI2D | 2 | Etu5, Etu12 |
| BIM | 1 | Etu4 |
| CCA | 1 | Etu9 |
| IMA | 1 | Etu8 |
| MIND | 2 | Etu10, Etu11 |
| QI | 1 | Etu0 |
| RES | 1 | Etu1 |
| SAR | 1 | Etu7 |
| SESI | 1 | Etu6 |
| STL | 2 | Etu2, Etu3 |

L'identité des deux affectations signifie qu'il existe une **unique affectation stable** sur cet exemple.

---

### Q6 – Vérification de la stabilité

La méthode `StabilityChecker.find_unstable_pairs(assignment)` teste toutes les paires (i, j) avec i ∉ assignment[j] :
- i préfère-t-il j à son affectation actuelle ? (`rank_etu[i][j] < rank_etu[i][j_i]`)
- j a-t-il une place libre, ou existe-t-il un étudiant w ∈ assignment[j] tel que j préfère i à w ? (`rank_spe[j][i] < max_{w} rank_spe[j][w]`)

Complexité : O(n × m × cap_max).

**Résultats :**
- GS côté étudiants : **0 paire instable** → affectation stable ✓
- GS côté parcours : **0 paire instable** → affectation stable ✓

---

### Q7 – Génération aléatoire

`RandomGenerator.generate_CE(n, m)` : pour chaque étudiant, permutation aléatoire de [0, m-1].  
`RandomGenerator.generate_CP(n, m)` : pour chaque parcours, permutation aléatoire de [0, n-1].  
`RandomGenerator.generate_balanced_capacities(n, m)` : cap_j = n//m (les n%m premiers ont cap_j+1), garantissant Σcap = n.

---

### Q8 – Mesure des temps de calcul

Résultats moyens (10 tests par valeur de n, m = 10 parcours, capacités équilibrées) :

| n | t etu (ms) | t parcours (ms) | iter. etu | iter. parcours |
|---|---|---|---|---|
| 200 | 0.22 | 0.36 | 264 | 868 |
| 400 | 0.21 | 0.52 | 505 | 1 946 |
| 600 | 0.32 | 0.86 | 705 | 3 068 |
| 800 | 0.49 | 1.37 | 932 | 4 374 |
| 1 000 | 0.52 | 1.48 | 1 130 | 5 434 |
| 1 200 | 0.59 | 1.78 | 1 339 | 6 540 |
| 1 400 | 0.89 | 2.16 | 1 562 | 7 419 |
| 1 600 | 0.91 | 2.72 | 1 773 | 8 999 |
| 1 800 | 1.12 | 2.84 | 1 976 | 9 694 |
| 2 000 | 1.15 | 3.04 | 2 209 | 10 593 |

Les courbes sont sauvegardées dans `performance_times.png` et `performance_iters.png`.

---

### Q9 – Complexité observée

Les temps croissent de façon **linéaire** en n pour les deux algorithmes (m = 10 fixé), ce qui est cohérent avec :
- GS côté étudiants : O(n × m × log(n/m)) ≈ O(n) pour m constant
- GS côté parcours : O(n × m) = O(n) pour m constant

Le ratio des temps spe/etu ≈ 2.6× s'explique par le fait que la version côté parcours effectue environ 5× plus de propositions (car les parcours doivent parcourir plus d'étudiants pour remplir leurs quotas face aux refus).

---

### Q10 – Nombre d'itérations

Les itérations croissent également **linéairement** en n :
- Côté étudiants : ≈ 1.1n propositions en moyenne (la plupart des étudiants sont acceptés rapidement)
- Côté parcours : ≈ 5.3n propositions en moyenne (les parcours contactent plus d'étudiants pour combler leur capacité)

Analyse théorique : dans le pire cas, un étudiant propose à tous les m parcours (n×m propositions). En pratique avec des préférences aléatoires, on observe O(n log(n/m)) propositions côté étudiants (phénomène de coupon collector), ce qui est cohérent avec les résultats.

---

### Q11 – PLNE maximisant l'utilité minimale

**Score de Borda** de l'étudiant i affecté au parcours j : `b_ij = m - 1 - rank_etu[i][j]` (1er choix → 9, dernier → 0).

Soit x_{ij} ∈ {0,1} : 1 si l'étudiant i est affecté au parcours j.

**PLNE Q11 :**

> **Maximiser** U_min
>
> **Sous les contraintes :**
> - U_min ≤ Σ_{j=0}^{9} b_{ij} · x_{ij},  ∀i ∈ {0,…,12}
> - Σ_{j=0}^{9} x_{ij} = 1,  ∀i  (chaque étudiant affecté à un seul parcours)
> - Σ_{i=0}^{12} x_{ij} ≤ cap_j,  ∀j  (respect des capacités)
> - x_{ij} ∈ {0,1}

**Résultat Gurobi :** utilité minimale optimale = **5** (vs 4 pour les affectations GS), utilité moyenne = 8.23 ; 3 paires instables.

---

### Q12 – PLNE maximisant la somme des utilités

Score de Borda du parcours j pour l'étudiant i : `c_{ji} = n - 1 - rank_spe[j][i]` (1er étudiant préféré → 12, dernier → 0).

**PLNE Q12 :**

> **Maximiser** Σ_{i,j} (b_{ij} + c_{ji}) · x_{ij}
>
> **Sous les mêmes contraintes d'affectation et de capacité.**

**Résultat Gurobi :** utilité totale (etu + parcours) = **213**, utilité moyenne étudiants = 7.77, utilité minimale étudiants = **4** ; 7 paires instables.

---

### Q13 – PLNE avec contrainte des k premiers choix

Un étudiant est dans ses k premiers choix si et seulement si son score Borda est ≥ m − k (car rang ≤ k−1 ⟺ borda ≥ m−1−(k−1) = m−k).

**PLNE Q13 (pour un k fixé) :**

> **Maximiser** Σ_{i,j} (b_{ij} + c_{ji}) · x_{ij}
>
> **Sous les contraintes d'affectation et de capacité, plus :**
> - Σ_{j=0}^{9} b_{ij} · x_{ij} ≥ m − k,  ∀i  (chaque étudiant dans ses k premiers choix)

---

### Q14 – Plus petit k pour un mariage parfait

On résout Q13 pour k = 1, 2, 3, … jusqu'à faisabilité :

| k | Faisable ? | Util. min étu. |
|---|---|---|
| 1 | Non | — |
| 2 | Non | — |
| 3 | Non | — |
| 4 | Non | — |
| **5** | **Oui** | **5** |

**Plus petit k = 5.** Affectation obtenue : AI2D={Etu7,Etu12}, BIM={Etu4}, CCA={Etu9}, IMA={Etu10}, MIND={Etu2,Etu11}, QI={Etu1}, RES={Etu8}, SAR={Etu6}, SESI={Etu0}, STL={Etu3,Etu5}. Utilité moyenne = 7.85, min = 5 ; 5 paires instables.

---

### Q15 – Comparaison des affectations

| Affectation | Util. moy. | Util. min. | Paires instables |
|---|---|---|---|
| GS côté étudiants | 7.85 | 4 | **0** (stable) |
| GS côté parcours | 7.85 | 4 | **0** (stable) |
| Q11 – maximin | **8.23** | **5** | 3 |
| Q12 – max somme | 7.77 | 4 | 7 |
| Q14 – k=5, max somme | 7.85 | **5** | 5 |

**Analyse :**
- Les deux affectations GS sont identiques et stables — elles sont donc optima-pareto parmi les affectations stables (ce cas particulier n'a qu'une seule affectation stable).
- Q11 améliore l'équité (utilité min passe de 4 à 5) mais brise la stabilité.
- Q12 maximise la satisfaction globale (étudiants + parcours) mais donne la même utilité min que GS avec plus d'instabilités.
- Q14 (k=5) offre le meilleur compromis équité/somme parmi les solutions PLNE : même utilité moyenne que GS, utilité min identique à Q11, au prix de 5 paires instables.

---

## 4. Jeux d'essais

| Jeu d'essai | Description |
|---|---|
| `PrefEtu.txt` + `PrefSpe.txt` | Instance réelle : 13 étudiants, 10 parcours, capacités [2,1,1,1,2,1,1,1,1,2] |
| Instances aléatoires | n ∈ {200, 400, …, 2000}, m = 10, capacités équilibrées, 10 tirages par n |

Les instances aléatoires sont reproductibles en fixant `random.seed(42)` (non imposé ici pour varier les mesures et avoir une moyenne représentative).

Pour valider la correction :
- Vérification `Σ cap_j = n` (matching parfait possible) sur toutes les instances.
- `StabilityChecker` renvoie 0 paire instable sur toutes les instances GS testées.
- Les deux algorithmes GS donnent toujours une affectation valide (chaque étudiant affecté à un seul parcours, capacités respectées).

---

## 5. Analyse des performances

**Temps de calcul** : les deux courbes sont linéaires en n pour m fixé, confirmant la complexité théorique O(n×m). La version côté parcours est ≈ 2.6× plus lente que côté étudiants à n=2000 (3.04 ms vs 1.15 ms), essentiellement car elle effectue ≈ 5× plus de propositions.

**Nombre d'itérations** : la croissance est également linéaire en n, cohérente avec la borne O(n×m). Le nombre moyen d'itérations reste bien en-dessous du pire cas (n×m = 20 000 pour n=2000) : ≈ 2 209 côté étudiants et ≈ 10 593 côté parcours à n=2000, soit respectivement ≈ 11% et ≈ 53% du pire cas.

**Conclusion** : l'algorithme côté étudiants est plus efficace en pratique grâce à la max-heap (opérations de remplacement en O(log cap)). L'algorithme côté parcours est conceptuellement plus simple (O(1) par proposition) mais nécessite davantage de propositions en raison de la dynamique du problème des hôpitaux.
