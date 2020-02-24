import streamlit as st

from pandas import DataFrame
from cmp.pycompiler import Grammar, EOF
from cmp.utils import Token, tokenizer
from grammalyzer import DerivationTree, LALR1Parser, LL1Parser, LR1Parser, SLR1Parser, table_to_dataframe

presentation = """
# Proyecto de Compilacion

# Grammar Analyzer WebApp

## Autores: 
    Alejandro Klever Clemente
    Miguel Angel Gonzalez Calles

## Grupo: C-311"""

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

example_aliases_2 = """num num -?[1-9][0-9]*
equal = =
plus + [+]"""

example_productions = """E %= E + plus + T | E + minus + T | T 
T %= T + star + F | T + div + F | F
F %= num | opar + E + cpar"""

example_productions_2 = """E %= T + X
X %= plus + T + X | minus + T + X | G.Epsilon
T %= F + Y
Y %= star + F + | div + F + Y | G.Epsilon
F %= num | opar + E + cpar"""

example_productions_3 = """E %=  A + equal + A | num
A %= num + plus + A | num"""


def exec_instructions(G, *instructions):
    for ins in instructions:
        exec(ins)


def terminals_input_control(option, options, input_terminals):
    terminals_id = {}
    terminals_regex = {}

    st.title('Grammar Analyzer App')
    if option != 'terminal id':
        aliases = st.text_area('Alias de los terminales: ', value=example_aliases)

        if aliases:
            aliases = [tuple(s.split()) for s in aliases.split('\n')]

            if option == 'terminal id + value':
                assert all(len(s) == 2 for s in aliases), f'{options[1]} option must have 2 words separated by space'
                terminals_id = {value: name for name, value in aliases}
            else:
                assert all(len(s) == 3 for s in aliases), f'{options[2]} option must have 3 words separated by space'
                terminals_id = {value: name for name, value, _ in aliases}
                terminals_regex = {value: regex for _, value, regex in aliases}
    else:
        terminals_id = {term: term for term in input_terminals.split()}

    return terminals_id, terminals_regex


def manual_input_app():
    ################
    # Declarations #
    ################
    G = Grammar()
    parsers = {'LL(1)': LL1Parser, 'SLR(1)': SLR1Parser, 'LR(1)': LR1Parser, 'LALR(1)': LALR1Parser}

    #################
    # Input Options #
    #################
    options = ('terminal id', 'terminal id + value', 'terminal id + value + regex')
    option = st.sidebar.selectbox('Entrada de los terminales', options, index=2)

    ###################
    # Parser Selector #
    ###################
    parser_type = st.sidebar.selectbox('Seleccione el algoritmo de Parsing', ('LL(1)', 'SLR(1)', 'LR(1)', 'LALR(1)'),
                                       index=1)

    ################################################
    # Start Symbol, Non terminal & terminals Input #
    ################################################
    start_symbol = st.sidebar.text_input('Simbolo inicial: ', value="E")
    input_nonterminals = st.sidebar.text_input('No Terminales :', value="T F")
    input_terminals = st.sidebar.text_input('Terminales :', value="num - + * / ( )  ")

    terminals_id, terminals_regex = terminals_input_control(option, options, input_terminals)

    ###################
    # Get Productions #
    ###################
    input_productions = st.text_area('Producciones :', value=example_productions)

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
    exec_instructions(G, inst1, inst2, inst3, input_productions)

    #########################
    # Preparacion del Lexer #
    #########################
    lexer = tokenizer(G, {t.Name: Token(t.Name, t) for t in G.terminals})

    ##########################
    # Preparacion del parser #
    ##########################
    ParserClass = parsers[parser_type]
    parser = ParserClass(G)

    if parser.ParserConstructionError:
        # Handle parsing error
        pass

    ####################
    # Fisrts & Follows #
    ####################
    if st.checkbox('Mostrar Firsts & Follows :'):
        # st.dataframe({'rojo': {'rojo': True}, 'azul': {'azul': True}})
        st.subheader("Firsts :")
        st.dataframe(set_to_dataframe(parser.G, parser.firsts))
        st.subheader("Follows :")
        st.dataframe(set_to_dataframe(parser.G, parser.follows))
        # st.dataframe(table_to_dataframe(parser.action))
        # st.dataframe(table_to_dataframe(parser.goto))

    text = st.text_input('Introduzca una cadena para analizar', value='num + num * num * ( num - num + num ) * num')

    if st.button('Analyze'):
        tokens = lexer(text)
        derivation = parser(tokens)
        st.graphviz_chart(str(DerivationTree(derivation, parser_type in ('SLR(1)', 'LR(1)', 'LALR(1)')).graph()))


def main():
    app_option = st.sidebar.selectbox('Choose an option', ('-', 'Manual Input', 'Load From File'), index=0)

    if app_option == '-':
        st.sidebar.success('Choose an option above')
        st.markdown(body=presentation)
    elif app_option == 'Manual Input':
        manual_input_app()
    else:
        pass


def set_to_dataframe(G: Grammar, first: dict):
    d = {}
    for alpha, firsts_set in first.items():
        for f in firsts_set:
            try:
                d[alpha][f] = True
            except KeyError:
                d[alpha] = {f: True}

        if firsts_set.contains_epsilon:
            try:
                d[alpha][G.Epsilon] = True
            except KeyError:
                d[alpha] = {G.Epsilon: True}

    return DataFrame.from_dict(d, orient='index')


if __name__ == "__main__":
    main()
