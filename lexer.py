import ply.lex as lex
import sys
import re

# sys.argv[1] en adelante son los argumentos
if len(sys.argv) < 2 or len(sys.argv) >= 3:
    print(f"\033[1;31mError!\033[0m You sent {len(sys.argv)} arguments.\n\033[1;33mUsage:\033[0m lexerpy [argument]")
    sys.exit(1)


file = sys.argv[1]

# Verify that file ends in .imperat
pattern = r".+\.imperat"

if not re.fullmatch(pattern, file):
    print(f"\033[1;31mError!\033[0m You didn't send an \033[1;34m.imperat\033[0m file")
    sys.exit(1)

with open(file, "r") as f:
    data = f.read()

tokens = (
    'TkIf',
    'TkWhile',
    'TkEnd',
    'TkFor',
    'TkPrint',
    'TkInt',
    'TkBool',
    'TkTrue',
    'TkFalse',
    'TkFunction',
    'TkId',
    'TkAsig',
    'TkNum',
    'TkString',
    'TkOBlock',
    'TkCBlock',
    'TkSoForth',
    'TkComma',
    'TkOpenPar',
    'TkClosePar',
    'TkSemicolon',
    'TkArrow',
    'TkGuard',
    'TkPlus',
    'TkMinus',
    'TkMult',
    'TkOr',
    'TkAnd',
    'TkNot',
    'TkLess',
    'TkLeq',
    'TkGeq',
    'TkGreater',
    'TkEqual',
    'TkNEqual',
    'TkOBracket',
    'TkCBracket',
    'TkTwoPoints',
    'TkApp',
)

reserved = {
    'if': 'TkIf',
    'while': 'TkWhile',
    'end': 'TkEnd',
    'for': 'TkFor',
    'print': 'TkPrint',
    'int': 'TkInt',
    'bool': 'TkBool',
    'true': 'TkTrue',
    'false': 'TkFalse',
    'function': 'TkFunction',
    'or': 'TkOr',
    'and': 'TkAnd',
}

# Function to find columns from a token
def find_column(input, token):
    last_cr = input.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        last_cr = -1
    return token.lexpos - last_cr

# Function to update lines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_TkAsig = r':='
t_TkOBlock = r'{'
t_TkCBlock = r'}'
t_TkSoForth = r'\.\.'
t_TkComma = r','
t_TkOpenPar = r'\('
t_TkClosePar = r'\)'
t_TkSemicolon = r';'
t_TkArrow = r'-->'
t_TkGuard = r'\[\]'

t_TkPlus = r'\+'
t_TkMinus = r'-'
t_TkMult = r'\*'
t_TkNot = r'!'
t_TkLeq = r'<='
t_TkLess = r'<'
t_TkGeq = r'>=' 
t_TkGreater = r'>' 
t_TkEqual = r'=='
t_TkNEqual = r'<>'
t_TkOBracket = r'\['
t_TkCBracket= r'\]'
t_TkTwoPoints = r':'
t_TkApp = r'\.'

def t_TkId(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'TkId')
    return t

def t_TkString(t):
    r'".*"'
    return t

def t_TkNum(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# This is how we manage errors
errors = []
def t_error(t):
    col = find_column(data, t)
    errors.append(f'\033[1;31mError:\033[0m Unexpected character "{t.value[0]}" in row {t.lineno}, column {col}')
    t.lexer.skip(1)

# We ignore empty char, tab and all comments using //
t_ignore = ' \t'
def t_COMMENT(t):
    r'//.*'
    pass

lexer = lex.lex()

lexer.input(data)

tokens = []
for tok in lexer:
    tokens.append(tok)

if errors:
    for e in errors:
        print(e)
    tokens=[]
else:
    for tok in tokens:
        col = find_column(data, tok)
        if(tok.type == "TkNum" or tok.type == "TkId" or tok.type == "TkString"):
            print(f"{tok.type}({tok.value}) {tok.lineno} {col}")
        else:
            print(f"{tok.type} {tok.lineno} {col}")

