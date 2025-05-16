import ply.lex as lex

tokens = (
    'TkIf',
    'TkWhile',
    'TkEnd',
    'TkFor',
    'TkId',
    'TkAsig',
)

# Function to update the line
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}' en fila {t.lineno}")
    t.lexer.skip(1)

t_TkIf  = r'if'
t_TkWhile  = r'while'
t_TkEnd = r'end'
t_TkFor = r'for'
t_TkAsig = r':='

def t_TkId(t):
    r'[a-zA-Z]+'
    return t

t_ignore = ' \t\n'

# Probar el lexer
data = 'if if    for     while :=  x \n xy'

lexer = lex.lex()

lexer.input(data)

for tok in lexer:
    print(f"{tok.type}({tok.value})")


