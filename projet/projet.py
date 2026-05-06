"""
LU3IN025 - Intelligence Artificielle et Jeux
TME 1 à 3 : Algorithme de Gale-Shapley et Programmation Linéaire en Nombres Entiers
Problème d'affectation des étudiants dans les parcours du Master Informatique
"""

import random
import time
import heapq
from collections import deque

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# =============================================================================
# Classe PreferenceData : lecture et stockage des données de préférences
# =============================================================================

class PreferenceData:
    """
    Lit et stocke les préférences des étudiants et des parcours.

    Attributs principaux :
      CE[i]     : liste des IDs de parcours ordonnée par préférence de l'étudiant i
      CP[j]     : liste des IDs d'étudiants ordonnée par préférence du parcours j
      capacities[j] : capacité d'accueil du parcours j
      rank_etu[i][j]: rang du parcours j dans les préférences de l'étudiant i (0=meilleur)
      rank_spe[j][i]: rang de l'étudiant i dans les préférences du parcours j (0=meilleur)
    """

    def __init__(self):
        self.n = 0
        self.m = 0
        self.CE = []
        self.CP = []
        self.capacities = []
        self.student_names = []
        self.spe_names = []
        self.rank_etu = []
        self.rank_spe = []

    def read_student_prefs(self, filename):
        """Q1 : Lit PrefEtu.txt et construit la matrice CE."""
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        self.n = int(lines[0].strip())
        self.CE = []
        self.student_names = []
        for line in lines[1:self.n + 1]:
            parts = line.split()
            self.student_names.append(parts[1])
            self.CE.append([int(x) for x in parts[2:]])
        return self.CE

    def read_spe_prefs(self, filename):
        """Q1 : Lit PrefSpe.txt et construit la matrice CP et les capacités."""
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        # Ligne 0 : NbEtu <n>
        n_check = int(lines[0].split()[1])
        assert n_check == self.n, "Incohérence dans le nombre d'étudiants"
        # Ligne 1 : Cap <c0> <c1> ...
        self.capacities = [int(x) for x in lines[1].split()[1:]]
        self.m = len(self.capacities)
        self.CP = []
        self.spe_names = []
        for line in lines[2:2 + self.m]:
            parts = line.split()
            self.spe_names.append(parts[1])
            self.CP.append([int(x) for x in parts[2:]])
        return self.CP

    def build_rank_matrices(self):
        """
        Construit les matrices inverses de classement pour des accès en O(1).
        rank_etu[i][j] = position du parcours j dans la liste de l'étudiant i
        rank_spe[j][i] = position de l'étudiant i dans la liste du parcours j
        """
        self.rank_etu = [[0] * self.m for _ in range(self.n)]
        for i in range(self.n):
            for pos, spe in enumerate(self.CE[i]):
                self.rank_etu[i][spe] = pos

        self.rank_spe = [[0] * self.n for _ in range(self.m)]
        for j in range(self.m):
            for pos, stu in enumerate(self.CP[j]):
                self.rank_spe[j][stu] = pos

        return self.rank_etu, self.rank_spe

    def display_assignment(self, assignment):
        """Affiche une affectation de manière lisible."""
        for j in range(self.m):
            students = sorted(assignment[j])
            names = [self.student_names[s] for s in students]
            print(f"  {self.spe_names[j]:6s} (cap {self.capacities[j]}): {names}")

    def assignment_to_current_spe(self, assignment):
        """Construit le tableau current_spe[i] à partir d'une affectation."""
        current_spe = {}
        for j, students in assignment.items():
            for i in students:
                current_spe[i] = j
        return current_spe


# =============================================================================
# Classe GaleShapleyStudentSide : GS côté étudiants
# =============================================================================

class GaleShapleyStudentSide:
    """
    Algorithme de Gale-Shapley côté étudiants pour le problème des hôpitaux.

    Structures de données choisies pour l'efficacité (Q2) :
    1. free_students (deque)   : O(1) pour prendre/rendre libre un étudiant
    2. next_proposal[i] (list) : O(1) pour trouver la prochaine proposition
    3. rank_spe[j][i] (list 2D): O(1) pour trouver le rang d'un étudiant dans un parcours
    4. assignment[j] (set)     : O(1) pour ajouter/retirer un étudiant
    5. worst_heap[j] (max-heap): O(log cap) pour trouver et remplacer l'étudiant le moins
                                  préféré du parcours (stocké comme (-rang, etudiant))

    Complexité : O(n × m × log(cap_max)) où n = nb étudiants, m = nb parcours
    En pratique avec capacités équilibrées (cap ≈ n/m) : O(n × m × log(n/m))
    """

    def __init__(self, CE, CP, capacities, rank_spe):
        self.CE = CE
        self.CP = CP
        self.capacities = capacities
        self.rank_spe = rank_spe
        self.n = len(CE)
        self.m = len(CP)

    def run(self):
        """
        Exécute GS côté étudiants.
        Retourne (assignment, iterations) :
          assignment : dict {id_parcours: set d'id_étudiants}
          iterations : nombre total de propositions effectuées
        """
        # 1. Tous les étudiants sont libres au départ
        free_students = deque(range(self.n))
        # 2. Indice de la prochaine proposition pour chaque étudiant
        next_proposal = [0] * self.n
        # 4. Affectation courante par parcours
        assignment = {j: set() for j in range(self.m)}
        # 5. Max-heap par parcours : (-rang_spe[j][i], i) → sommet = pire étudiant
        worst_heap = [[] for _ in range(self.m)]

        iterations = 0

        while free_students:
            i = free_students.popleft()

            if next_proposal[i] >= self.m:
                # Étudiant rejeté par tous les parcours (ne doit pas arriver si Σcap = n)
                continue

            j = self.CE[i][next_proposal[i]]   # prochain parcours à qui proposer
            next_proposal[i] += 1
            iterations += 1

            if len(assignment[j]) < self.capacities[j]:
                # Parcours j a de la place → accepte l'étudiant i
                assignment[j].add(i)
                heapq.heappush(worst_heap[j], (-self.rank_spe[j][i], i))
            else:
                # Parcours j est plein → compare i avec le pire étudiant actuel
                neg_worst_rank, worst_stu = worst_heap[j][0]
                worst_rank = -neg_worst_rank
                if self.rank_spe[j][i] < worst_rank:
                    # i est meilleur que le pire → on remplace
                    heapq.heapreplace(worst_heap[j], (-self.rank_spe[j][i], i))
                    assignment[j].remove(worst_stu)
                    assignment[j].add(i)
                    free_students.append(worst_stu)   # le pire redevient libre
                else:
                    # i est rejeté → reste libre et propose au suivant
                    free_students.append(i)

        return assignment, iterations


# =============================================================================
# Classe GaleShapleySpeSide : GS côté parcours
# =============================================================================

class GaleShapleySpeSide:
    """
    Algorithme de Gale-Shapley côté parcours pour le problème des hôpitaux.

    Structures de données (Q4) :
    1. active (set)            : ensemble des parcours sous-remplis avec des candidats
    2. next_proposal[j] (list) : O(1) pour trouver la prochaine proposition
    3. rank_etu[i][j] (list 2D): O(1) pour comparer deux parcours du point de vue d'un étudiant
    4. current_spe[i] (list)   : O(1) pour trouver le parcours actuel d'un étudiant
    5. assignment[j] (set)     : O(1) pour ajouter/retirer un étudiant

    Complexité : O(n × m) — chaque parcours propose au plus n fois, chaque proposition O(1)
    """

    def __init__(self, CE, CP, capacities, rank_etu):
        self.CE = CE
        self.CP = CP
        self.capacities = capacities
        self.rank_etu = rank_etu
        self.n = len(CE)
        self.m = len(CP)

    def run(self):
        """
        Exécute GS côté parcours.
        Retourne (assignment, iterations).
        """
        next_proposal = [0] * self.m
        current_spe = [None] * self.n    # parcours actuel de chaque étudiant
        assignment = {j: set() for j in range(self.m)}

        # Tous les parcours qui ont de la capacité démarrent actifs
        active = {j for j in range(self.m) if self.capacities[j] > 0}

        iterations = 0

        while active:
            j = next(iter(active))
            active.discard(j)

            # Le parcours j propose jusqu'à être plein ou avoir épuisé sa liste
            while len(assignment[j]) < self.capacities[j] and next_proposal[j] < self.n:
                i = self.CP[j][next_proposal[j]]
                next_proposal[j] += 1
                iterations += 1

                if current_spe[i] is None:
                    # Étudiant i est libre → accepte j
                    assignment[j].add(i)
                    current_spe[i] = j
                else:
                    j_prime = current_spe[i]
                    if self.rank_etu[i][j] < self.rank_etu[i][j_prime]:
                        # i préfère j à j' → change d'affectation
                        assignment[j_prime].remove(i)
                        assignment[j].add(i)
                        current_spe[i] = j
                        # j' a perdu un étudiant, le réactiver si nécessaire
                        if (len(assignment[j_prime]) < self.capacities[j_prime]
                                and next_proposal[j_prime] < self.n):
                            active.add(j_prime)
                    # else : i reste avec j' — j continuera sa boucle interne

        return assignment, iterations


# =============================================================================
# Classe StabilityChecker : vérification de la stabilité
# =============================================================================

class StabilityChecker:
    """
    Vérifie la stabilité d'une affectation et retourne les paires instables.

    Une paire (i, j) est instable si :
    - L'étudiant i n'est pas affecté à j
    - i préfère j à son affectation courante
    - j préfère i à l'un de ses étudiants actuels (ou j a une place libre)

    Complexité : O(n × m) grâce au pré-calcul du pire rang par parcours.
    """

    def __init__(self, CE, CP, capacities, rank_etu, rank_spe):
        self.CE = CE
        self.CP = CP
        self.capacities = capacities
        self.rank_etu = rank_etu
        self.rank_spe = rank_spe
        self.n = len(CE)
        self.m = len(CP)

    def find_unstable_pairs(self, assignment):
        """Retourne la liste des paires (i, j) instables."""
        current_spe = {}
        for j, students in assignment.items():
            for i in students:
                current_spe[i] = j

        # Pré-calculer le rang du pire étudiant de chaque parcours en O(n) au total
        # (évite de recalculer max(...) O(cap) fois pour le même j dans la boucle)
        worst_rank_in = {
            j: max(self.rank_spe[j][w] for w in students) if students else -1
            for j, students in assignment.items()
        }

        unstable = []
        for i in range(self.n):
            j_i = current_spe.get(i)
            for j in range(self.m):
                if j_i == j:
                    continue
                if j_i is None:
                    i_prefers_j = True
                else:
                    i_prefers_j = self.rank_etu[i][j] < self.rank_etu[i][j_i]
                if not i_prefers_j:
                    continue
                if len(assignment[j]) < self.capacities[j]:
                    unstable.append((i, j))
                elif self.rank_spe[j][i] < worst_rank_in[j]:
                    unstable.append((i, j))

        return unstable


# =============================================================================
# Classe RandomGenerator : génération d'instances aléatoires (Q7)
# =============================================================================

class RandomGenerator:
    """Génère des instances aléatoires de préférences pour les tests de performance."""

    @staticmethod
    def generate_CE(n, m):
        """Matrice CE aléatoire : n étudiants × m parcours."""
        CE = []
        template = list(range(m))
        for _ in range(n):
            prefs = template[:]
            random.shuffle(prefs)
            CE.append(prefs)
        return CE

    @staticmethod
    def generate_CP(n, m):
        """Matrice CP aléatoire : m parcours × n étudiants."""
        CP = []
        template = list(range(n))
        for _ in range(m):
            prefs = template[:]
            random.shuffle(prefs)
            CP.append(prefs)
        return CP

    @staticmethod
    def generate_balanced_capacities(n, m):
        """Capacités équilibrées sommant à n : base = n//m, les premiers avec +1."""
        base = n // m
        remainder = n % m
        return [base + (1 if i < remainder else 0) for i in range(m)]

    @staticmethod
    def build_rank_etu(CE, m):
        n = len(CE)
        rank = [[0] * m for _ in range(n)]
        for i in range(n):
            for pos, spe in enumerate(CE[i]):
                rank[i][spe] = pos
        return rank

    @staticmethod
    def build_rank_spe(CP, n):
        m = len(CP)
        rank = [[0] * n for _ in range(m)]
        for j in range(m):
            for pos, stu in enumerate(CP[j]):
                rank[j][stu] = pos
        return rank


# =============================================================================
# Classe PerformanceMeasurer : mesure et tracé des performances (Q8-Q10)
# =============================================================================

class PerformanceMeasurer:
    """
    Mesure le temps de calcul et le nombre d'itérations des algorithmes GS
    pour différentes valeurs de n, et génère les courbes de performance.
    """

    def __init__(self, m=10):
        self.m = m

    def measure(self, n_values, n_tests=10):
        """
        Pour chaque n dans n_values, exécute n_tests fois les deux algorithmes
        et retourne les moyennes de temps et d'itérations.
        """
        results = {
            'n_values': n_values,
            'times_student': [], 'times_spe': [],
            'iters_student': [], 'iters_spe': [],
        }

        for n in n_values:
            caps = RandomGenerator.generate_balanced_capacities(n, self.m)
            t_stu_list, t_spe_list, it_stu_list, it_spe_list = [], [], [], []

            for _ in range(n_tests):
                CE = RandomGenerator.generate_CE(n, self.m)
                CP = RandomGenerator.generate_CP(n, self.m)
                rank_etu = RandomGenerator.build_rank_etu(CE, self.m)
                rank_spe = RandomGenerator.build_rank_spe(CP, n)

                gs_stu = GaleShapleyStudentSide(CE, CP, caps, rank_spe)
                t0 = time.perf_counter()
                _, iters = gs_stu.run()
                t_stu_list.append(time.perf_counter() - t0)
                it_stu_list.append(iters)

                gs_spe = GaleShapleySpeSide(CE, CP, caps, rank_etu)
                t0 = time.perf_counter()
                _, iters = gs_spe.run()
                t_spe_list.append(time.perf_counter() - t0)
                it_spe_list.append(iters)

            results['times_student'].append(sum(t_stu_list) / n_tests)
            results['times_spe'].append(sum(t_spe_list) / n_tests)
            results['iters_student'].append(sum(it_stu_list) / n_tests)
            results['iters_spe'].append(sum(it_spe_list) / n_tests)

        return results

    def plot_times(self, results, filename='performance_times.png'):
        """Trace le temps moyen en fonction de n."""
        plt.figure(figsize=(8, 5))
        plt.plot(results['n_values'], results['times_student'], 'b-o',
                 label='GS côté étudiants')
        plt.plot(results['n_values'], results['times_spe'], 'r-s',
                 label='GS côté parcours')
        plt.xlabel("Nombre d'étudiants (n)")
        plt.ylabel('Temps de calcul moyen (s)')
        plt.title('Performance de Gale-Shapley en fonction de n')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        return filename

    def plot_iterations(self, results, filename='performance_iters.png'):
        """Trace le nombre moyen d'itérations en fonction de n."""
        plt.figure(figsize=(8, 5))
        plt.plot(results['n_values'], results['iters_student'], 'b-o',
                 label='GS côté étudiants')
        plt.plot(results['n_values'], results['iters_spe'], 'r-s',
                 label='GS côté parcours')
        plt.xlabel("Nombre d'étudiants (n)")
        plt.ylabel("Nombre d'itérations moyen")
        plt.title("Nombre d'itérations de Gale-Shapley en fonction de n")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        return filename


# =============================================================================
# Classe PLNESolver : résolution des PLNE avec Gurobi (Q11-Q14)
# =============================================================================

class PLNESolver:
    """
    Résout les formulations PLNE avec Gurobi.

    Score de Borda de l'étudiant i affecté au parcours j :
      borda_etu(i, j) = m - 1 - rank_etu[i][j]
      (1er choix → m-1, dernier choix → 0)

    Score de Borda du parcours j ayant l'étudiant i :
      borda_spe(j, i) = n - 1 - rank_spe[j][i]
      (1er choix → n-1, dernier choix → 0)
    """

    def __init__(self, CE, CP, capacities, rank_etu, rank_spe):
        self.CE = CE
        self.CP = CP
        self.capacities = capacities
        self.rank_etu = rank_etu
        self.rank_spe = rank_spe
        self.n = len(CE)
        self.m = len(CP)

        # Pré-calcul des scores de Borda
        self.bs_etu = [
            [self.m - 1 - rank_etu[i][j] for j in range(self.m)]
            for i in range(self.n)
        ]
        self.bs_spe = [
            [self.n - 1 - rank_spe[j][i] for i in range(self.n)]
            for j in range(self.m)
        ]

    def _base_model(self, name=""):
        """Crée un modèle Gurobi avec les contraintes de base."""
        import gurobipy as gp
        from gurobipy import GRB
        model = gp.Model(name)
        model.setParam('OutputFlag', 0)

        x = model.addVars(self.n, self.m, vtype=GRB.BINARY, name="x")

        # Chaque étudiant affecté à exactement un parcours
        for i in range(self.n):
            model.addConstr(gp.quicksum(x[i, j] for j in range(self.m)) == 1)

        # Contraintes de capacité
        for j in range(self.m):
            model.addConstr(gp.quicksum(x[i, j] for i in range(self.n)) <= self.capacities[j])

        return model, x, GRB

    def _extract_assignment(self, x):
        """Extrait l'affectation de la solution Gurobi."""
        assignment = {j: set() for j in range(self.m)}
        for i in range(self.n):
            for j in range(self.m):
                if x[i, j].X > 0.5:
                    assignment[j].add(i)
        return assignment

    def student_utils(self, assignment):
        """Retourne la liste des utilités (Borda) de chaque étudiant dans une affectation."""
        utils = []
        for j, students in assignment.items():
            for i in students:
                utils.append(self.bs_etu[i][j])
        return utils

    def q11_maximize_min_utility(self):
        """
        Q11 : Maximise l'utilité minimale des étudiants.

        Variables : x[i,j] ∈ {0,1}, u_min ≥ 0
        Maximiser : u_min
        Sous :
          u_min ≤ Σ_j bs_etu[i][j] * x[i,j]   ∀i
          Σ_j x[i,j] = 1                         ∀i
          Σ_i x[i,j] ≤ cap[j]                   ∀j
        """
        import gurobipy as gp
        from gurobipy import GRB
        model, x, GRB = self._base_model("Q11_maximin")

        u_min = model.addVar(name="u_min", lb=0.0)
        for i in range(self.n):
            model.addConstr(
                u_min <= gp.quicksum(self.bs_etu[i][j] * x[i, j] for j in range(self.m))
            )

        model.setObjective(u_min, GRB.MAXIMIZE)
        model.optimize()

        if model.status == GRB.OPTIMAL:
            return self._extract_assignment(x), u_min.X
        return None, None

    def q12_maximize_sum_utility(self):
        """
        Q12 : Maximise la somme des utilités (étudiants + parcours).

        Maximiser : Σ_i Σ_j x[i,j] * (bs_etu[i][j] + bs_spe[j][i])
        """
        import gurobipy as gp
        from gurobipy import GRB
        model, x, GRB = self._base_model("Q12_maxsum")

        obj = gp.quicksum(
            (self.bs_etu[i][j] + self.bs_spe[j][i]) * x[i, j]
            for i in range(self.n) for j in range(self.m)
        )
        model.setObjective(obj, GRB.MAXIMIZE)
        model.optimize()

        if model.status == GRB.OPTIMAL:
            return self._extract_assignment(x), model.ObjVal
        return None, None

    def q13_maximize_sum_with_k(self, k):
        """
        Q13/Q14 : Maximise la somme des utilités avec contrainte que chaque étudiant
        obtient l'un de ses k premiers choix.

        Contrainte ajoutée : Σ_j bs_etu[i][j] * x[i,j] ≥ m - k   ∀i
        (un étudiant est dans ses k premiers choix ssi son score Borda ≥ m - k)
        """
        import gurobipy as gp
        from gurobipy import GRB
        model, x, GRB = self._base_model(f"Q13_k{k}")

        # Chaque étudiant doit être dans ses k premiers choix
        for i in range(self.n):
            model.addConstr(
                gp.quicksum(self.bs_etu[i][j] * x[i, j] for j in range(self.m)) >= self.m - k
            )

        obj = gp.quicksum(
            (self.bs_etu[i][j] + self.bs_spe[j][i]) * x[i, j]
            for i in range(self.n) for j in range(self.m)
        )
        model.setObjective(obj, GRB.MAXIMIZE)
        model.optimize()

        if model.status == GRB.OPTIMAL:
            return self._extract_assignment(x), model.ObjVal
        return None, None   # INFEASIBLE ou autre


# =============================================================================
# Fonctions utilitaires d'affichage
# =============================================================================

def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def compute_stats(utils, label=""):
    avg = sum(utils) / len(utils) if utils else 0
    mn = min(utils) if utils else 0
    print(f"  {label}Utilité moyenne étudiants : {avg:.2f} | minimale : {mn}")


# =============================================================================
# Fonction principale
# =============================================================================

def main():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ------------------------------------------------------------------
    # Q1 : Lecture des fichiers
    # ------------------------------------------------------------------
    print_section("Q1 : Lecture des fichiers de préférences")

    data = PreferenceData()
    data.read_student_prefs(os.path.join(base_dir, "PrefEtu.txt"))
    data.read_spe_prefs(os.path.join(base_dir, "PrefSpe.txt"))
    data.build_rank_matrices()

    print(f"  {data.n} étudiants, {data.m} parcours")
    print(f"  Capacités : {dict(zip(data.spe_names, data.capacities))}")
    print(f"  Somme des capacités : {sum(data.capacities)}")

    # ------------------------------------------------------------------
    # Q3 : GS côté étudiants
    # ------------------------------------------------------------------
    print_section("Q3 : Gale-Shapley côté étudiants")

    gs_stu = GaleShapleyStudentSide(data.CE, data.CP, data.capacities, data.rank_spe)
    assignment_stu, iters_stu = gs_stu.run()

    print(f"  Itérations (propositions) : {iters_stu}")
    data.display_assignment(assignment_stu)

    # ------------------------------------------------------------------
    # Q4/Q5 : GS côté parcours
    # ------------------------------------------------------------------
    print_section("Q4/Q5 : Gale-Shapley côté parcours")

    gs_spe = GaleShapleySpeSide(data.CE, data.CP, data.capacities, data.rank_etu)
    assignment_spe, iters_spe = gs_spe.run()

    print(f"  Itérations (propositions) : {iters_spe}")
    data.display_assignment(assignment_spe)

    # ------------------------------------------------------------------
    # Q6 : Vérification de la stabilité
    # ------------------------------------------------------------------
    print_section("Q6 : Vérification de la stabilité")

    checker = StabilityChecker(
        data.CE, data.CP, data.capacities, data.rank_etu, data.rank_spe
    )

    unstable_stu = checker.find_unstable_pairs(assignment_stu)
    unstable_spe = checker.find_unstable_pairs(assignment_spe)

    print(f"  GS côté étudiants : {len(unstable_stu)} paire(s) instable(s)")
    if unstable_stu:
        for i, j in unstable_stu:
            print(f"    ({data.student_names[i]}, {data.spe_names[j]})")

    print(f"  GS côté parcours  : {len(unstable_spe)} paire(s) instable(s)")
    if unstable_spe:
        for i, j in unstable_spe:
            print(f"    ({data.student_names[i]}, {data.spe_names[j]})")

    # ------------------------------------------------------------------
    # Q7-Q10 : Performance
    # ------------------------------------------------------------------
    print_section("Q7-Q10 : Génération aléatoire et mesure des performances")

    n_values = list(range(200, 2001, 200))
    measurer = PerformanceMeasurer(m=data.m)
    print(f"  Calcul en cours (n de {n_values[0]} à {n_values[-1]}, 10 tests/valeur)...")

    results = measurer.measure(n_values, n_tests=10)

    time_file = os.path.join(base_dir, 'performance_times.png')
    iter_file = os.path.join(base_dir, 'performance_iters.png')
    measurer.plot_times(results, time_file)
    measurer.plot_iterations(results, iter_file)

    print(f"  Courbes sauvegardées : {time_file}, {iter_file}")
    print(f"  {'n':>5}  {'t_etu (ms)':>12}  {'t_spe (ms)':>12}  {'iters_etu':>10}  {'iters_spe':>10}")
    for k, n in enumerate(n_values):
        t_e = results['times_student'][k] * 1000
        t_s = results['times_spe'][k] * 1000
        it_e = results['iters_student'][k]
        it_s = results['iters_spe'][k]
        print(f"  {n:>5}  {t_e:>12.2f}  {t_s:>12.2f}  {it_e:>10.0f}  {it_s:>10.0f}")

    # ------------------------------------------------------------------
    # Q11-Q15 : PLNE avec Gurobi
    # ------------------------------------------------------------------
    print_section("Q11-Q15 : Programmation Linéaire en Nombres Entiers (Gurobi)")

    try:
        plne = PLNESolver(
            data.CE, data.CP, data.capacities, data.rank_etu, data.rank_spe
        )

        # Q11
        print("\n  [Q11] Maximisation de l'utilité minimale des étudiants")
        aff_q11, u_min_q11 = plne.q11_maximize_min_utility()
        if aff_q11:
            utils_q11 = plne.student_utils(aff_q11)
            unstable_q11 = checker.find_unstable_pairs(aff_q11)
            print(f"  Utilité minimale optimale : {u_min_q11:.0f}")
            compute_stats(utils_q11, "  ")
            print(f"  Paires instables : {len(unstable_q11)}")
            data.display_assignment(aff_q11)

        # Q12
        print("\n  [Q12] Maximisation de la somme des utilités (étudiants + parcours)")
        aff_q12, obj_q12 = plne.q12_maximize_sum_utility()
        if aff_q12:
            utils_q12 = plne.student_utils(aff_q12)
            unstable_q12 = checker.find_unstable_pairs(aff_q12)
            print(f"  Utilité totale (etu+spe) : {obj_q12:.0f}")
            compute_stats(utils_q12, "  ")
            print(f"  Paires instables : {len(unstable_q12)}")
            data.display_assignment(aff_q12)

        # Q13/Q14 : trouver le plus petit k donnant un mariage parfait
        print("\n  [Q13/Q14] Recherche du plus petit k pour un mariage parfait")
        best_k = None
        best_aff_k = None
        best_obj_k = None

        for k in range(1, data.m + 1):
            aff_k, obj_k = plne.q13_maximize_sum_with_k(k)
            feasible = (aff_k is not None)
            print(f"    k={k} : {'faisable' if feasible else 'infaisable'}", end="")
            if feasible:
                utils_k = plne.student_utils(aff_k)
                print(f"  (util. min étudiants = {min(utils_k)})")
                if best_k is None:
                    best_k = k
                    best_aff_k = aff_k
                    best_obj_k = obj_k
            else:
                print()

        if best_aff_k is not None:
            utils_best = plne.student_utils(best_aff_k)
            unstable_best = checker.find_unstable_pairs(best_aff_k)
            print(f"\n  Plus petit k : {best_k}")
            compute_stats(utils_best, "  ")
            print(f"  Paires instables : {len(unstable_best)}")
            data.display_assignment(best_aff_k)

        # Q15 : Comparaison des affectations
        print_section("Q15 : Comparaison des affectations")

        def summarize(label, aff, checker, plne):
            utils = plne.student_utils(aff)
            unstable = checker.find_unstable_pairs(aff)
            avg = sum(utils) / len(utils) if utils else 0
            print(f"  {label:<35} util. moy. = {avg:.2f}  util. min. = {min(utils)}  "
                  f"paires instables = {len(unstable)}")

        summarize("GS côté étudiants", assignment_stu, checker, plne)
        summarize("GS côté parcours", assignment_spe, checker, plne)
        if aff_q11:
            summarize(f"Q11 (maximin)", aff_q11, checker, plne)
        if aff_q12:
            summarize("Q12 (max somme utilités)", aff_q12, checker, plne)
        if best_aff_k:
            summarize(f"Q14 (k={best_k}, max somme + équité)", best_aff_k, checker, plne)

    except ImportError:
        print("  Gurobi non disponible — Q11-Q15 non exécutés.")
    except Exception as e:
        import traceback
        print(f"  Erreur Gurobi : {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
