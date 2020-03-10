import json

import streamlit as st
from pandas import DataFrame

from cmp.pycompiler import Grammar
from cmp.utils import Token, tokenizer
from examples import (AritmethicStartSymbol, AritmethicNonTerminalsLR, AritmethicTerminals, AritmethicProductionsLR,
                      AritmethicAliases)
from grammalyzer import (LLDerivationTree, LRDerivationTree, LALR1Parser, LL1Parser, LR1Parser, SLR1Parser, Lexer,
                         delete_common_prefix, delete_inmidiate_left_recursion, clean_grammar)
from grammalyzer.conflict import LLConflictStringGenerator, LRConflictStringGenerator
from regex.utils import RegularGrammar

PRESENTATION = """
# Proyecto de Compilacion

# Grammar Analyzer WebApp

## Autores: 
    Alejandro Klever Clemente
    Miguel Angel Gonzalez Calles

## Grupo: C-311"""


def show_grammar(G):
    ptroductions2string = []
    for key, productions in {str(nt): nt.productions for nt in G.nonTerminals}.items():
        productions = [str(p.Right) for p in productions]
        s = f'{key} -> {" | ".join(productions)}'
        ptroductions2string.append(s)

    body = f"""
#### Terminales : 
        {' '.join(t.Name for t in G.terminals)}
#### No Terminales : 
        {' '.join(t.Name for t in G.nonTerminals)}
#### Producciones :
"""
    for x in ptroductions2string:
        body += '        ' + x + '\n'
    st.markdown(body)


def encode_value(value):
    try:
        action, tag = value
        if action == SLR1Parser.SHIFT:
            return 'S' + str(tag)
        elif action == SLR1Parser.REDUCE:
            return repr(tag)
        elif action == SLR1Parser.OK:
            return action
        else:
            return value
    except TypeError:
        return value


def lrtable_to_dataframe(table):
    d = {}
    for (state, symbol), value in table.items():
        value = encode_value(value)
        try:
            d[state][symbol] = value
        except KeyError:
            d[state] = {symbol: value}

    return DataFrame.from_dict(d, orient='index', dtype=str)


def lltable_to_dataframe(table):
    d = {}
    for (x, s), p in table.items():
        value = repr(p[0])
        try:
            d[x][s] = value
        except KeyError:
            d[x] = {s: value}

    return DataFrame.from_dict(d, orient='index', dtype=str)


def set_to_dataframe(G, sset):
    terminals = G.terminals + [G.Epsilon]
    nonterminals = set(G.nonTerminals)

    d = {key: {t: '-' for t in terminals} for key in sset}
    for alpha, firsts_set in sset.items():

        if hasattr(alpha, 'IsNonTerminal') and alpha not in nonterminals:
            del d[alpha]
            continue

        for f in firsts_set:
            d[alpha][f] = 'X'

        if firsts_set.contains_epsilon:
            d[alpha][G.Epsilon] = 'X'
    return DataFrame.from_dict(d, orient='index', dtype=str)


# noinspection PyUnusedLocal
def exec_instructions(G, *instructions):
    for ins in instructions:
        exec(ins)


def terminals_input_control(option, options, input_terminals):
    """
    Se encarga del tomar y dar formato a los terminales
    """
    terminals_id = {}
    terminals_regex = {}

    st.title('Grammar Analyzer App')
    if option != 'terminal id':
        aliases = st.text_area('Alias de los terminales: ', value=AritmethicAliases)

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


def modify_grammar(G):
    if st.checkbox('Modificar Gramatica'):
        modifications = st.multiselect('Escoja modificaciones', ('Eliminar prefijos comunes',
                                                                 'Eliminar recursion izquierda inmediata',
                                                                 'Eliminar producciones innecesarias'))
        if 'Eliminar prefijos comunes' in modifications:
            st.subheader('Gramatica sin prefijos comunes')
            GG = delete_common_prefix(G)
            show_grammar(GG)

        if 'Eliminar recursion izquierda inmediata' in modifications:
            st.subheader('Gramatica recursion izquierda inmediata')
            GG = delete_inmidiate_left_recursion(G)
            show_grammar(GG)

        if 'Eliminar producciones innecesarias' in modifications:
            st.subheader('Gramatica sin producciones innecesarias')
            GG = clean_grammar(G)
            show_grammar(GG)


def deal_with_conflict(parser, parser_type):
    if parser_type == 'LL(1)':
        conflictgen = LLConflictStringGenerator(parser)
        x, s = conflictgen.conflict
        st.error(f'Parser LL(1) con conflicto en la entrada : ({x}, {s})')
        body = f"""# Cadenas de conflicto :
## Con la produccion : {repr(conflictgen.prod1)}
        {conflictgen.s1}
## Con la produccion : {repr(conflictgen.prod2)}
        {conflictgen.s2}
"""
        st.markdown(body)
    else:
        conflictgen = LRConflictStringGenerator(parser)
        x, s = conflictgen.conflict
        st.error(f'Parser {parser_type} con conflicto en la entrada : ({x}, {s})')
        body = f"""# Cadena de conflicto :
### Con las producciones : {conflictgen.conflict.value1} y {conflictgen.conflict.value2}
        {conflictgen.path}
"""
        st.markdown(body)


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
    start_symbol = st.sidebar.text_input('Simbolo inicial: ', value=AritmethicStartSymbol)
    input_nonterminals = st.sidebar.text_input('No Terminales :', value=AritmethicNonTerminalsLR)
    input_terminals = st.sidebar.text_input('Terminales :', value=AritmethicTerminals)

    terminals_id, terminals_regex = terminals_input_control(option, options, input_terminals)

    ###################
    # Get Productions #
    ###################
    input_productions = st.text_area('Producciones :', value=AritmethicProductionsLR)

    nonterminals_variables = ', '.join(input_nonterminals.split())
    terminal_variables = ', '.join(terminals_id[term] for term in input_terminals.split())

    #####################################################
    # Declarando instrucciones para ejecutar con exec() #
    #####################################################
    inst1 = f'{start_symbol} = G.NonTerminal("{start_symbol}", True)'
    if len(input_nonterminals) == 1:
        inst2 = f'{nonterminals_variables} = G.NonTerminal("{input_nonterminals}")'
    else:
        inst2 = f'{nonterminals_variables} = G.NonTerminals("{input_nonterminals}")'
    inst3 = f'{terminal_variables} = G.Terminals("{input_terminals}")'

    ##########
    # exec() #
    ##########
    exec_instructions(G, inst1, inst2, inst3, input_productions)

    #########################
    # Preparacion del Lexer #
    #########################
    if terminals_regex:
        table = [(G[t], re) for t, re in terminals_regex.items()] + [('space', '  *'), ]
        lexer = Lexer(table, G.EOF)
    else:
        lexer = tokenizer(G, {t.Name: Token(t.Name, t) for t in G.terminals})

    ##########################
    # Preparacion del parser #
    ##########################
    ParserClass = parsers[parser_type]
    parser = ParserClass(G)

    ##########
    # Salvar #
    ##########
    gName = st.sidebar.text_input("Nombre del archivo")
    if st.sidebar.button("Salvar"):
        try:
            f = open(gName + '.json', 'x')
            s = G.to_json
            json.dump(s, f, indent=4)
            st.sidebar.success(f'Salvado {gName}.json')
        except FileExistsError:
            st.sidebar.error('Ya existe un archivo con ese nombre')

    ############################
    # Regular Grammar Checking #
    ############################
    re_grammar = RegularGrammar(G)
    if re_grammar.valid:
        st.sidebar.success("Esta Gramatica es Regular")
        dfa = re_grammar.dfa
        regex = re_grammar.regex
        if st.checkbox('Mostrar DFA de la Gramatica'):
            st.graphviz_chart(str(dfa.graph()))
        if st.checkbox('Mostrar la expresion regular'):
            st.latex(regex)

    ###########################
    # Visualizar la gramatica #
    ###########################
    if st.checkbox('Mostrar Gramatica'):
        show_grammar(G)

    ####################
    # Fisrts & Follows #
    ####################
    if st.checkbox('Mostrar Firsts & Follows'):
        st.subheader("Firsts :")
        st.dataframe(set_to_dataframe(parser.G, parser.firsts))
        st.subheader("Follows :")
        st.dataframe(set_to_dataframe(parser.G, parser.follows))

    ##################
    #  Parsing Table #
    ##################
    if st.checkbox('Mostrar Tabla de Parsing'):
        if parser_type == 'LL(1)':
            st.subheader("Table :")
            st.dataframe(lltable_to_dataframe(parser.table))
        else:
            st.subheader("Action :")
            st.dataframe(lrtable_to_dataframe(parser.action))
            st.subheader("Goto :")
            st.dataframe(lrtable_to_dataframe(parser.goto))

    ###############
    # Automata LR #
    ###############
    if parser_type != 'LL(1)':
        if st.checkbox('Mostrar Automata LR'):
            st.graphviz_chart(str(parser.automaton.graph()))
        dtree = LRDerivationTree
    else:
        dtree = LLDerivationTree

    ################################
    # Modificacion de la Gramatica #
    ################################
    modify_grammar(G)

    ####################
    # Parsing Conflict #
    ####################
    if parser.conflict is not None:
        deal_with_conflict(parser, parser_type)

    else:
        ####################
        # Analizar cadenas #
        ####################
        text = st.text_input('Introduzca una cadena para analizar', value='1 + 1 * 1 * ( 1 - 1 + 1 ) * 1')

        if st.button('Analyze'):
            tokens = [t for t in lexer(text) if t.token_type != 'space']
            derivation = parser(tokens)
            st.graphviz_chart(str(dtree(derivation).graph()))


def load_from_file_app():
    file = st.file_uploader('Cargar gramatica desde archivo')
    st.write(type(file))


def main():
    app_option = st.sidebar.selectbox('Choose an option', ('-', 'Manual Input'), index=0)

    if app_option == '-':
        st.sidebar.success('Choose an option above')
        st.markdown(body=PRESENTATION)
    else:
        try:
            manual_input_app()
        except Exception as e:
            st.error(e.args[0])


if __name__ == "__main__":
    main()
