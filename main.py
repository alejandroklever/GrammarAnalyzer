import streamlit as st

from cmp.pycompiler import Grammar
from cmp.utils import Token, tokenizer
from GrammarAnalyzer import DerivationTree, LALR1Parser, LL1Parser, LR1Parser, SLR1Parser


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

example_productions = """E %= E + plus + T | T | E + minus + T 
T %= T + star + F | F | T + div + F
F %= num | opar + E + cpar"""

################
# Declarations #
################
terminals_regex = {}
terminals_id = {}
parsers = {'LL(1)': LL1Parser, 'SLR(1)': SLR1Parser, 'LR(1)': LR1Parser, 'LALR(1)': LALR1Parser}
G = Grammar()

def exec_instructions(*instructions):
    for ins in instructions:
        exec(ins)

def manual_input_app():
    #################
    # Input Options #
    #################
    options = ('terminal id', 'terminal id + value', 'terminal id + value + regex')
    option = st.sidebar.selectbox('Entrada de los terminales', options, index=2)

    ###################
    # Parser Selector #
    ###################
    parser_type = st.sidebar.selectbox('Seleccione el algoritmo de Parsing', ('LL(1)', 'SLR(1)', 'LR(1)', 'LALR(1)'), index=1)

    ################################################
    # Start Symbol, Non terminal & terminals Input #
    ################################################
    start_symbol = st.sidebar.text_input('Simbolo inicial: ', value="E")
    input_nonterminals = st.sidebar.text_input('No Terminales :', value="T F")
    input_terminals = st.sidebar.text_input('Terminales :', value="+ - * / ( ) num")
    show_grammar = st.sidebar.checkbox('Show Grammar')

    st.title('Grammar Analyzer App')
    if option != 'terminal id':
        aliases = st.text_area('Alias de los terminales: ', value=example_aliases)

        if aliases:
            aliases = [tuple(s.split()) for s in aliases.split('\n')]

            if option == 'terminal id + value':
                assert all(len(s) == 2 for s in aliases), f'{options[1]} option most have 2 words separated by space'
                terminals_id = {value: name for name, value in aliases}
            else:
                assert all(len(s) == 3 for s in aliases), f'{options[2]} option must have 3 words separated by space'
                terminals_id = {value: name for name, value, _ in aliases}
                terminals_regex = {value: regex for _, value, regex in aliases}
    else:
        terminals_id = {term: term for term in input_terminals.split()}


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
    exec_instructions(inst1, inst2, inst3, input_productions)

    if show_grammar:
        st.subheader('Grammar')
        st.text(G)

    lexer = tokenizer(G, {t.Name: Token(t.Name, t) for t in G.terminals})

    text = st.text_input('Introduzca una cadena para analizar', value='num + num')

    if st.button('Analyze'):
        tokens = lexer(text)

        st.subheader('Tokens:')
        st.text('\n'.join(str(t) for t in tokens))

        ParserClass = parsers[parser_type]
        st.write(parser_type)
        parser = ParserClass(G)
        derivation = parser(tokens)

        radio = st.sidebar.radio("Parsing Data:", ("Show Derivation Tree", "Show Automata", "Run Examples"))
        if radio == 'Show Derivation Tree':
            st.subheader('Left Parse:')
            [repr(x) for x in derivation]
            st.subheader('Firsts:')
            {repr(k): repr(v) for k, v in parser.Firsts.items()}
    

def main():
    app_option = st.sidebar.selectbox('Choose an option', ('-', 'Manual Input', 'Load From File'), index=0)


    if app_option == '-':
        st.sidebar.success('Choose an option above')

        st.markdown(body='''
        # Proyecto de Compilacion

        # Grammar Analyzer WebApp

        ## Autor: Alejandro Klever Clemente
        
        ## Grupo: C-311''')
    elif app_option == 'Manual Input':
        manual_input_app()
    else:
        pass


if __name__ == "__main__":
    main()
