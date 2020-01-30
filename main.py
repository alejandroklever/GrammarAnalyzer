import streamlit as st

from GrammarAnalyzer import LL1Parser, SLR1Parser, LR1Parser, LALR1Parser, DerivationTree
from cmp.pycompiler import Grammar
from cmp.utils import Token, tokenizer

############
# Examples #
############
example_aliases = """plus + [+]
minus - [-]
star * [*]
div / [/]
opar ( [(]
cpar ) [)]
num num [1-9][0-9]*"""

example_productions = """E %= E + plus + T | E + minus + T | T | G.Epsilon
T %= T + star + F | T + div + F | F | G.Epsilon
F %= num | opar + E + cpar"""

################
# Declarations #
################
terminals_regex = {}
terminals_id = {}
parsers = {'LL(1)': LL1Parser, 'SLR(1)': SLR1Parser, 'LR(1)': LR1Parser, 'LALR(1)': LALR1Parser}
G = Grammar()

#################
# Input Options #
#################
options = ("terminal id", "terminal id + value", "terminal id + value + regex")
option = st.sidebar.selectbox("Entrada de los terminales", options, index=2)
option_index = options.index(option)

start_symbol = st.sidebar.text_input('Simbolo inicial: ', value="E")
input_nonterminals = st.sidebar.text_input('No Terminales :', value="T F")
input_terminals = st.sidebar.text_input('Terminales :', value="+ - * / ( ) num")
input_productions = st.text_area('Producciones :')

if option_index:
    aliases = st.sidebar.text_area('Alias de los terminales: ', value=example_aliases)

    if aliases:
        aliases = [tuple(s.split()) for s in aliases.split('\n')]

        if option_index == 1:
            assert all(len(s) == 2 for s in aliases), f'{options[1]} option most have 2 words separated by space'
            terminals_id = {value: name for name, value in aliases}
        else:
            assert all(len(s) == 3 for s in aliases), f'{options[2]} option must have 3 words separated by space'
            terminals_id = {value: name for name, value, _ in aliases}
            terminals_regex = {value: regex for _, value, regex in aliases}
else:
    terminals_id = {term: term for term in input_terminals.split()}

nonterminals_variables = ', '.join(input_nonterminals.split())
terminal_variables = ', '.join(terminals_id[term] for term in input_terminals.split())

#####################################################
# Declarando instrucciones para ejecutar con exec() #
#####################################################
inst1 = f'{start_symbol} = G.NonTerminal("{start_symbol}", True)'
inst2 = f'{nonterminals_variables} = G.NonTerminals("{input_nonterminals}")'
inst3 = f'{terminal_variables} = G.Terminals("{input_terminals}")'

##########
# exec() #
##########
exec(inst1)
exec(inst2)
exec(inst3)
exec(input_productions)

st.title('Grammar')
st.text(G)

lexer = tokenizer(G, {t.Name: Token(t.Name, t) for t in G.terminals})

text = st.text_input('Introduzca una cadena para analizar')
parser_type = st.selectbox('Seleccione el algoritmo de Parsing', ('LL(1)', 'SLR(1)', 'LR(1)', 'LALR(1)'), index=1)

if st.button('Compute'):
    tokens = lexer(text)

    st.header('Tokens:')
    s = '\n'.join([str(t) for t in tokens])
    st.text(s)

    ParserClass = parsers[parser_type]
    parser = ParserClass(G)
    derivation = parser(tokens)

    st.header('Left Parse:')
    [repr(x) for x in derivation]

    # dtree = DerivationTree(left_parse)

    # st.header('Derivation Tree:')
    # st.text(str(dtree))
