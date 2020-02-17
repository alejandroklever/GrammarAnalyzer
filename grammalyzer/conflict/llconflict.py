from collections import deque
from typing import Dict, Tuple, List

from cmp.pycompiler import Sentence, Production, Grammar, NonTerminal, Terminal, Symbol
from grammalyzer.parsing import LL1Parser

################
# Custom Types #
################
ParsingTable = Dict[Tuple[NonTerminal, Terminal], List[Production]]


def compute_sentence_forms(G: Grammar):
    sentence = {t: Sentence(t) for t in G.terminals}

    change = True
    while change:
        n = len(sentence)
        for production in G.Productions:
            head, body = production

            if head in sentence:
                continue

            if body.IsEpsilon or all(symbol in sentence for symbol in body):
                sentence[head] = Sentence(*[sentence[symbol] for symbol in body])

        change = n != len(sentence)

    return sentence


def compute_fixxed_sentence_forms(G: Grammar, t: Terminal, sentence_forms: Dict[Symbol, Sentence]):
    fixxed_sentence = {t: Sentence(t)}

    change = True
    while change:
        n = len(fixxed_sentence)
        for production in G.Productions:
            head, body = production

            if head in fixxed_sentence:
                continue

            if not body.IsEpsilon and body[0] in fixxed_sentence:
                fixxed_sentence[head] = Sentence(
                    *([fixxed_sentence[body[0]]] + [sentence_forms[symbol] for symbol in body[1:]]))

        change = n != len(fixxed_sentence)

    return fixxed_sentence


def shortest_production_path(G: Grammar, x: NonTerminal):
    queue = deque([x])
    sentence_form = {x: Sentence(x)}
    production_path = {x: [Production(x, Sentence(x))]}  # Eliminar esta linea de testeo

    productions = set(G.Productions)
    while queue:
        current = queue.popleft()

        visited_productions = set()
        for production in productions:

            head, body = production

            if head in sentence_form:
                continue

            sentence = Sentence()
            current_belong = False
            for i, symbol in enumerate(body):
                if symbol == current:
                    current_belong = True
                    sentence += sentence_form[current]
                else:
                    sentence += symbol

            if current_belong:
                queue.append(head)
                sentence_form[head] = sentence
                production_path[head] = [production] + production_path[current]
                visited_productions.add(production)

        productions -= visited_productions

    assert G.startSymbol in sentence_form, f'{x} is not reacheable from start symbol {G.startSymbol}'

    return sentence_form[G.startSymbol], production_path[G.startSymbol][:-1]


class LLConflictStringGenerator:
    def __init__(self, parser: LL1Parser):
        assert parser.build_parser_error, 'Expected parser with conflict...'
        self.G = parser.G
        self.table = parser.table
        self.key = parser.conflict

    def generate_conflict(self):
        G = self.G
        x, s = self.key
        # table = self.table
        #
        # conflict0, conflict1 = table[x, s][0], table[x, s][1]
        sentence, _ = shortest_production_path(G, x)
        sentence_forms = compute_sentence_forms(G)
        sentence_forms_fixxed = compute_fixxed_sentence_forms(G, s, sentence_forms)

        new_sentence = Sentence()
        for symbol in sentence:
            if symbol == x:
                new_sentence += sentence_forms_fixxed[symbol]
            else:
                new_sentence += sentence_forms[symbol]
        return new_sentence
