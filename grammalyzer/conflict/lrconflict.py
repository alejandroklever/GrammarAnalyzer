from enum import Enum, auto
from typing import List

from cmp.automata import State
from cmp.pycompiler import Terminal, NonTerminal


def transpose_automaton(states: List[State]):
    transpose = {s: {} for s in states}


def automaton_back_tracking(state: State, x: NonTerminal, t: Terminal):
    states = [s for s in state]


class ConflictType(Enum):
    ReduceReduce = auto()
    ShiftReduce = auto()


class LRConflictStringGenerator:
    def __init__(self):
        pass
