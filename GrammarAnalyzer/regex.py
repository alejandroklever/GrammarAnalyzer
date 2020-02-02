from cmp.utils import Token


def regex_tokenizer(text, G, skip_whitespaces=True):
    tokens = []
    fixed_tokens = { lex: Token(lex, G[lex]) for lex in '| * ( ) ε [ ] ? + -'.split()}
    open_pos = 0
    inside_squares = False
    for i, char in enumerate(text):
        if skip_whitespaces and char.isspace():
            continue
        
        if not inside_squares:
            if char in (']',  '-') or char not in fixed_tokens:
                tokens.append(Token(char, G['symbol']))
            else:
                tokens.append(fixed_tokens[char])
            
            open_pos = i
            inside_squares = char == '['
        
        else:
            if char in (']', '-'):
                if char == '-' and ((i + 1 < len(text) and text[i + 1] == ']') or text[i - 1] == '['):
                        tokens.append(Token(char, G['symbol']))
                else:
                    tokens.append(fixed_tokens[char])
            else:
                tokens.append(Token(char, G['symbol']))

            inside_squares = char != ']'
    
    if inside_squares:
        raise Exception(f'Unterminated character set at position {open_pos}')
        
    tokens.append(Token('$', G.EOF))
    return tokens