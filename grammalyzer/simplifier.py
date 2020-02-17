from cmp.pycompiler import Grammar, Sentence, SentenceList


# from GrammarAnalyzer import LR1Parser, ShiftReduceParser
# from Regex.automata import DFA
# from Regex.regex import Regex, regex_tokenizer

def delete_common_prefix(G: Grammar):
    # Algoritmo para eliminar los prefijos comunes de las producciones con la misma cabecera
    # Por cada no terminal busca si dos de sus produciones tiene prefijos comunes
    for elem in G.nonTerminals:
        Change = True
        primes = ''
        while Change:
            Change = False
            for item in elem.productions:
                Continue = False
                for item2 in elem.productions:
                    if item != item2:
                        LPC = 0
                        for i in range((min(len(item.Right), len(item2.Right)))):
                            if item.Right[i] == item2.Right[i]:
                                LPC += 1
                            else:
                                break
                        # En caso de que si tengan prefijos comunes se realiza el siguiente cambio:
                        # E -> aA | aB
                        # Entonces se cambia por :
                        # E -> aE'
                        # E' -> A | B
                        if LPC > 0:
                            primes += '\''
                            Temp = G.NonTerminal(f"{elem.Name}{primes}", False)
                            elem.productions.remove(item)
                            elem.productions.remove(item2)
                            G.Productions.remove(item)
                            G.Productions.remove(item2)
                            elem %= Sentence(*item.Right[0:LPC] + (Temp,))
                            alpha = item.Right[LPC:]
                            bheta = item2.Right[LPC:]
                            if len(alpha) == 0:
                                Temp %= G.Epsilon
                            else:
                                Temp %= Sentence(*alpha)
                            if len(bheta) == 0:
                                Temp %= G.Epsilon
                            else:
                                Temp %= Sentence(*bheta)
                            Change = True
                            Continue = True
                            break
                if Continue:
                    continue
    return G


def delete_inmidiate_left_recursion(G: Grammar):
    # Algoritmo para eliminar la recursion izquierda inmediata
    # Sria conveniente adaptarlo para que funciona sin crar una gramatica nueva pero en un principio es funcional
    Gnew = Grammar()
    Gnew.terminals = G.terminals

    for elem in G.nonTerminals:
        for item in elem.productions:
            if len(item.Right) > 0 and item.Right[0] == elem:
                # para cada no terminal con recursion izquierda inmediata creamos un nuevo terminal
                # A -> Ab | c
                # c y b formas oracionales sin A en el principio
                A = Gnew.NonTerminal(elem.Name, elem == G.startSymbol)
                B = Gnew.NonTerminal(f"{elem.Name}'", False)
                # B == A`
                # Las producciones de A son separadas en produciones de A y B de manera equivalente de la siguiente manera
                for prod in elem.productions:
                    if len(prod.Right) > 0 and prod.Right[0] == elem:
                        ##las que tengan recursion izquierda
                        B %= Sentence(*(prod.Right[1:] + (B,)))
                        # A` -> bA`
                    else:
                        A %= prod.Right + B
                        # A ->cA`
                B %= Gnew.Epsilon
                # A1 ->bA` | epsilon
                break
        else:
            # si no tiene recursion izquierda inmediata mantengo el no terminal
            A = Gnew.NonTerminal(elem.Name)
            for item in elem.productions:
                A %= item.Right
    return Gnew


G = Grammar()
E = G.NonTerminal('E', True)
T, F = G.NonTerminals('T F')
plus, minus, star, div, opar, cpar, num = G.Terminals('+ - * / ( ) int')

E %= E + plus + E | E + star + E | T
T %= num + opar + E + cpar | num | num + star + num | num + star + num + star
print("Probando eliminacion de prefijos comunes")
print(delete_common_prefix(G))

G = Grammar()
E = G.NonTerminal('E', True)
T, F = G.NonTerminals('T F')
plus, minus, star, div, opar, cpar, num = G.Terminals('+ - * / ( ) int')

E %= E + plus + T | T  # | E + minus + T
T %= T + star + F | F  # | T + div + F
F %= num | opar + E + cpar
print("\n\nProbando recursion izquierda inmediata")
print(delete_inmidiate_left_recursion(G))


def clean_grammar(G: Grammar):
    # El metodo de limpiar la gramatica Esta compuesto por varios pasos, sus nombres son suficientemente descriptivos
    G = delete_epsilon(G)
    G = EliminateUnitProductions(G)
    G = EliminateNonTerminalVariables(G)
    G = EliminateNonReacheableVariables(G)
    return G


def delete_epsilon(G: Grammar):
    # para eliminar las epsilon produciones encontramos el conjunto de los elementos nuleables
    # estos elementos son aquellos que tras una o mas produccions se vuelvan epsilon
    # A ->* epsilon => A es nulleable
    nullable = {}
    change = True
    while change:
        n = len(nullable)
        for head, body in G.Productions:

            if head in nullable:
                continue

            if len(body) == 0:
                nullable[head] = True
            else:
                nullable[head] = all(symbol in nullable for symbol in body)
        change = n != len(nullable)
    # Dado que tenemos los elementos nulleables para todas las produciones
    # si una produccion tiene un elemento nulleable esta es sustituida:
    # por esta misma produccion y la produccion sin el elemento nulleabe
    # Las epsilon producciones son eliminadas
    for elem in G.nonTerminals:
        Que = [x for x in elem.productions]
        Dic = {}
        while len(Que) > 0:
            production = Que.pop()
            if len(production.Right) == 0:
                G.Productions.remove(production)
                elem.productions.remove(production)
            else:
                for i, elem2 in enumerate(production.Right):
                    try:
                        if nullable[elem2]:
                            Add_Production(elem, Sentence(*(production.Right[0:max(i, 0)] + production.Right[i + 1:])), Dic, Que,
                                           True)
                    except KeyError:
                        pass
    return G


def Add_Production(NonTerminal, Sentence, Dic, Que=None, Enque=False):
    ## Metodo auxiliar para agregar nuevas produciones a la gramatica
    # Tambien actualiza la cola si Enque = true y el diccionario de elementos usados
    try:
        Dic[Sentence]
    except KeyError:
        Dic[Sentence] = True
        if len(Sentence) > 0:
            NonTerminal %= Sentence
        if Enque:
            Que.append(NonTerminal.productions[-1])


def EliminateUnitProductions(G: Grammar):
    ## para eliminar cada producion unitaria de la forma:
    ## A -> B
    ## B -> C | D | EF
    ## Simplemete "Subimos las produciones unitarias"
    ## O sea la adelantamos pues no es necesario producir B para que esta produzca e resto o se:
    ## A -> C | D | EF
    ## B -> C | D | EF

    Change = True
    while Change:
        Change = False
        for Prod in G.Productions:
            if len(Prod.Right) == 1 and Prod.Right[0] in G.nonTerminals:
                G.Productions.remove(Prod)
                Prod.Left.productions.remove(Prod)
                for P in Prod.Right[0].productions:
                    Prod.Left %= P.Right
                Change = True
    return G


def EliminateNonTerminalVariables(G: Grammar):
    ## Todas aquellos no terminales que no deriven en algun string terminal tras 1 o mas producciones
    ## No son necesarias pues las cadenas siempre estaran formadas unicaente por terminales
    ## y produciones que no generen terminales son inconsistentes con esta verdad
    ## por tanto no aportan informacion al lenguaje
    ## Y no son necesarias en la gramatica

    ## Computamos el conjunto de las produciones que derivan en terminales tra una o mas produciones
    ## La demostracion de la correctitud de este algoritmo puede ser inductiva
    ## buscamos las cadenas que terminen en terminales tras una produccion luego tras dos y asi sucesivamente
    DerivToTerminal = {}
    Change = True
    while Change:
        Change = False
        for Nonterminal in G.nonTerminals:
            for Prod in Nonterminal.productions:
                for elem in Prod.Right:
                    if elem not in G.terminals:
                        try:
                            DerivToTerminal[elem]
                        except KeyError:
                            break
                else:
                    try:
                        DerivToTerminal[Nonterminal]
                    except KeyError:
                        DerivToTerminal[Nonterminal] = True
                        Change = True

    ##Las produciones posean uno de los terminales que no derivan en string terminales son incosistentes
    ## Pues estas no terminarian en un string terminal
    ## Ya sea si lo poseen en la cabecera como en el cuerpo  de la produccion
    ## estas producciones inconsistentes son guardadas en Removable
    Removable = []
    for Prod in G.Productions:
        try:
            DerivToTerminal[Prod.Left]
            for Elem in Prod.Right:
                if Elem not in G.terminals:
                    try:
                        DerivToTerminal[Elem]
                    except KeyError:
                        Removable.append(Prod)
        except KeyError:
            Removable.append(Prod)

    ## Son removidas de la gramatica las producciones y no terminales inconsistentes
    for P in Removable:
        G.Productions.remove(P)
        P.Left.productions.remove(P)

    for Nonterminal in G.nonTerminals:
        if len(Nonterminal.productions) == 0:
            G.nonTerminals.remove(Nonterminal)

    return G


def EliminateNonReacheableVariables(G: Grammar):
    ##Evidentemente los elementos que no pueden ser alcanzados por una o mas producciones del caracter inicial
    ##No son necesarias pues nunca son utilizadas para generar ningun elemento del lenguaje
    ## estos elementos inalcanzables pueden ser tanto terminales como no terminales

    Que = [G.startSymbol]
    S_NTer = set([G.startSymbol])
    S_Ter = set()
    # hayamos los terminales y no terminales alcanzables
    while len(Que) > 0:
        Element = Que.pop()
        for Prod in Element.productions:
            for Elem2 in Prod.Right:
                if Elem2 in G.nonTerminals:
                    if Elem2 not in S_NTer:
                        S_NTer.add(Elem2)
                        Que.append(Elem2)
                else:
                    S_Ter.add(Elem2)
    # Eliminamos las producciones con elementos no alcanzables
    Removable = []
    for Prod in G.Productions:
        if Prod.Left not in S_NTer:
            Removable.append(Prod)
    for P in Removable:
        G.Productions.remove(P)

    # Ahora removemos los no terminales no alcanzables
    Removable = []
    for N in G.nonTerminals:
        if N not in S_NTer:
            Removable.append(N)
    for P in Removable:
        G.nonTerminals.remove(P)

    # Ahora removemos los terminales no alcanzables
    Removable = []
    for N in G.terminals:
        if N not in S_Ter:
            Removable.append(N)
    for P in Removable:
        G.terminals.remove(P)

    ##Klever es necesario hacerlo asi como lo escribi
    ## no se puede hacer en el mismo ciclo de recorrer los terminales pues si los remueves ahi el iterados
    ## se marea y te saltas elementos
    return G


G = Grammar()
S = G.NonTerminal('S', True)
A, B, C, D, F = G.NonTerminals('A B C D F')
a, b, d, f = G.Terminals('a b d f')

S %= A + B + C
A %= a + A | G.Epsilon
B %= b + B | G.Epsilon
C %= G.Epsilon
D %= d + D | f
F %= f

print("\n\nCleaned Gramar")
print(clean_grammar(G))
