import ply.lex as lex
import sys
import re

#  ================================
# | Team:                          |
# | David Díaz / 20-10019          |
# | Alan Argotte / 19-10664        |
#  ================================

# Verify arguments
if len(sys.argv) < 2 or len(sys.argv) >= 3:
    print(f"Error: You sent {len(sys.argv)} arguments.\nUsage: python lexer.py [argument]")
    sys.exit(1)

file = sys.argv[1]

# Verify that file ends in .imperat
pattern = r".+\.imperat"

if not re.fullmatch(pattern, file):
    print(f"Error: You didn't send an .imperat file")
    sys.exit(1)

# Read data file
with open(file, "r") as f:
    data = f.read()

# Declaring Tokens
tokens = (
    'TkIf',
    'TkFi',
    'TkWhile',
    'TkEnd',
    'TkFor',
    'TkPrint',
    'TkInt',
    'TkBool',
    'TkTrue',
    'TkFalse',
    'TkFunction',
    'TkSkip',
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

# Reserved words
reserved = {
    'if': 'TkIf',
    'fi': 'TkFi',
    'while': 'TkWhile',
    'end': 'TkEnd',
    'for': 'TkFor',
    'print': 'TkPrint',
    'int': 'TkInt',
    'bool': 'TkBool',
    'true': 'TkTrue',
    'false': 'TkFalse',
    'skip': 'TkSkip',
    'function': 'TkFunction',
    'or': 'TkOr',
    'and': 'TkAnd',
}

# Function to calculate token's column
def find_column(input, token):
    last_cr = input.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        last_cr = -1
    return token.lexpos - last_cr

# Function to update rows
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Regex section to identify tokens
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

# We ignore empty char, tab and all comments using //
t_ignore = ' \t'
def t_COMMENT(t):
    r'//.*'
    pass

# Regex functions section to identify tokens
def t_TkId(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'TkId')
    return t

def t_TkString(t):
    r'"([^"\\\n]|(\\n|\\\"|\\\\))*"'
    return t

def t_TkNum(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# This is how we manage errors
errors = []
def t_error(t):
    col = find_column(data, t)
    errors.append(f'Error: Unexpected character "{t.value[0]}" in row {t.lineno}, column {col}') # Appending errors in array errors
    t.lexer.skip(1)

lexer = lex.lex()
lexer.input(data)

# Create a token array that will store tokens
tokens = []
for tok in lexer:
    tokens.append(tok)

# If errors array is not empty, then we only print errors
if errors:
    for e in errors:
        print(e)
    tokens=[]
# If errors array is empty, then we print tokens
else:
    for tok in tokens:
        col = find_column(data, tok)
        if(tok.type == "TkNum" or tok.type == "TkId" or tok.type == "TkString"):
            if(tok.type == "TkId"):
                print(f'{tok.type}("{tok.value}") {tok.lineno} {col}')
            else:
                print(f"{tok.type}({tok.value}) {tok.lineno} {col}")
        else:
            print(f"{tok.type} {tok.lineno} {col}")