# GrammarAnalyzer
## University of Havana
## Compilation Project
### Topic:
A simple Streamlit application for grammar analysis, automaton visualization, and try parsers LL(1), SLR(1), LR(1), LALR(1).
### Abstract:
A compilation class project to analyze the behavior of LL (1), SLR (1), LR (1), LALR (1) parser with different grammar. 

Given an input grammar, and a parsing algorithm, the following results will be presented:
- If the grammar belongs to the family of parseable grammar by type of parser, if not, a string will be delivered that reflects the conflict between the grammar and the parsing algorithm.
- If the grammar is regular then the deterministic finite automaton will be shown and the regular expression that represents the language that this grammar generates.
- Access to the firsts and follow sets of each grammar.
- Show the parsing table.
- Given string belonging to the language generated by the grammar, its derivation tree will be shown.
- In the case of parser SLR (1), LR (1) and LARL (1), the deterministic finite automaton that recognizes the viable prefixes of the given grammar will be shown.
- Modify the grammar to eliminate common prefixes, immediate left recursion and unnecessary productions.
- Save the grammar in a .json file.
### Authors:
    Alejandro Klever Clemente
    Miguel Angel Gonzalez Calles
    
### How to use?
Run the command line ``stremalit run main.py``, and the magic will appear.
