import ply.yacc as yacc
import sys
import re

# Get the token map from the lexer.  This is required.
from lexer import tokens, lexer

#  ================================
# | Team:                          |
# | David Díaz / 20-10019          |
# | Alan Argotte / 19-10664        |
#  ================================ 

lexer.lineno = 1

if len(sys.argv) < 2 or len(sys.argv) >= 3:
    print(f"Error: You sent {len(sys.argv)} arguments.\nUsage: python parser.py [argument]")
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

precedence = (
    ('left', 'TkOr'),
    ('left', 'TkAnd'),
    ('left', 'TkEqual', 'TkNEqual'),
    ('nonassoc', 'TkLess', 'TkLeq', 'TkGreater', 'TkGeq'),
    ('left', 'TkPlus', 'TkMinus'),
    ('left', 'TkMult'),
    ('nonassoc', 'TkApp'),
    ('right', 'TkNot'),
    ('right', 'UMinus')
)

def p_program(p):
    '''program : TkOBlock declaration_list TkSemicolon statement_list TkCBlock
                | TkOBlock statement_list TkCBlock'''
    if(len(p) == 6):
        p[0] = ("Block", ("Declare", p[2]), (p[4]))
    else:
        p[0] = ("Block", (p[2]))



def p_declaration_list(p):
    '''declaration_list : declaration_list TkSemicolon declaration
                        | declaration'''
    if len(p) == 4:
        p[0] = ('Sequencing', p[1], p[3])
    else:
        p[0] = p[1]   


def p_declaration(p):
    '''declaration : TkInt variable_list
                    | TkBool variable_list'''
    p[0] = (p[2] + ' : ' + p[1]) 


def p_declaration_function(p):
    '''declaration : TkFunction TkOBracket TkSoForth TkNum TkCBracket variable_list'''
    p[0] = (p[6] + ' : ' + p[1] + '[..Literal: ' + str(p[4]) + ']')


def p_variable_list(p):
    '''variable_list : variable_list TkComma variable
                        | variable'''
    if len(p) == 4:
        p[0] = p[1] + ', ' + p[3]
    else:
        p[0] = p[1]


def p_variable(p):
    '''variable : TkId'''
    p[0] = p[1]


def p_statement_list(p):
    '''statement_list : statement_list TkSemicolon statement
                        | statement'''
    if len(p) == 4:
        p[0] = ('Sequencing', p[1], p[3])
    else:
        p[0] = p[1]


def p_statement_asig(p):
    '''statement : TkId TkAsig expression
                    | TkId TkAsig expression_list
                    | TkId TkAsig function_mod'''
    p[0] = ("Asig", "Ident: " + p[1], p[3])


def p_statement_if(p):
    '''statement : TkIf if_body TkFi'''
    p[0] = ("If", p[2])


def p_if_body(p):
    '''if_body : if_body TkGuard expression TkArrow statement_list
                | expression TkArrow statement_list'''
    if(len(p) == 6):
        p[0] = ("Guard", p[1], ("Then", p[3], p[5]))
    else:
        p[0] = ("Then", p[1], p[3])


def p_statement_while(p):
    '''statement : TkWhile expression TkArrow statement_list TkEnd'''
    p[0] = ("While", ("Then", p[2], p[4]))


def p_statement_print(p):
    '''statement : TkPrint expression
                | TkPrint string'''
    p[0] = ("Print", p[2])


def p_statement_skip(p):
    '''statement : TkSkip'''
    p[0] = ('skip')


def p_string_binop(p):
    '''string : string TkPlus string
                | string TkPlus expression
                | expression TkPlus string'''
    p[0] = ('Plus', p[1], p[3])

def p_string(p):
    '''string : TkString'''
    p[0] = ('String: ' + p[1])


def p_string_parenthesis(p):
    '''string : TkOpenPar TkString TkClosePar'''
    p[0] = ('String: ' + p[2])


def p_statement_program(p):
    '''statement : program'''
    p[0] = p[1]


def p_expression_list(p):
    '''expression_list : expression_list TkComma expression
                        | expression TkComma expression'''
    if len(p) == 4:
        p[0] = ("Comma", p[1], p[3]) 


def p_expression_binop(p):
    '''expression : expression TkPlus expression
                    | expression TkMinus expression
                    | expression TkMult expression
                    | expression TkAnd expression
                    | expression TkOr expression
                    | expression TkEqual expression
                    | expression TkNEqual expression
                    | TkNot expression
                    | TkMinus expression %prec UMinus
                    | expression TkLess expression
                    | expression TkGreater expression
                    | expression TkLeq expression
                    | expression TkGeq expression'''
    if(p[1] == '!'):
        p[0] = ('Not', p[2])
    elif(p[1] == '-'):
        p[0] = ('Minus', p[2])
    elif(p[2]=='+'):
        p[0] = ('Plus', p[1], p[3])
    elif(p[2]=='*'):
        p[0] = ('Mult', p[1], p[3])
    elif(p[2]=='-'):
        p[0] = ('Minus', p[1], p[3])
    elif(p[2]=='=='):
        p[0] = ('Equal', p[1], p[3])
    elif(p[2]=='<>'):
        p[0] = ('NotEqual', p[1], p[3])
    elif(p[2]=='<='):
        p[0] = ('Leq', p[1], p[3])
    elif(p[2]=='<'):
        p[0] = ('Less', p[1], p[3])
    elif(p[2]=='>='):
        p[0] = ('Geq', p[1], p[3])
    elif(p[2]=='>'):
        p[0] = ('Greater', p[1], p[3])
    elif(p[2]=='and'):
        p[0] = ('And', p[1], p[3])
    elif(p[2]=='or'):
        p[0] = ('Or', p[1], p[3])


def p_expression_app(p):
    '''expression : TkId TkApp expression'''
    p[0] = ("App", "Ident: " + p[1], p[3])

def p_expression_function_app(p):
    '''expression : function_mod TkApp expression'''
    p[0] = ("App", p[1], p[3])

def p_function_mod(p):
    '''function_mod : function_mod TkOpenPar two_points TkClosePar'''
    p[0] = ("WriteFunction", p[1], p[3])


def p_function_mod_base(p):
    '''function_mod : TkId TkOpenPar two_points TkClosePar'''
    p[0] = ("WriteFunction", "Ident: " + p[1], p[3])


def p_two_points(p):
    '''two_points : expression TkTwoPoints expression'''
    p[0] = ("TwoPoints", p[1], p[3])


def p_expression_num(p):
    '''expression : TkNum'''
    p[0] = ('Literal: ' + p[1])


def p_expression_id(p):
    '''expression : TkId'''
    p[0] = ('Ident: ' + p[1])


def p_expression_parens(p):
    '''expression : TkOpenPar expression TkClosePar'''
    p[0] = p[2]


def p_expression_def(p):
    '''expression : TkTrue
                    | TkFalse'''
    p[0] = ('Literal: ' + p[1])


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Function to calculate token's column
def find_column(input, token):
    last_cr = input.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        last_cr = -1
    return token.lexpos - last_cr

# Array to save errors
errors = []
def p_error(p):
    if p:
        col = find_column(data, p)
        errors.append(f"Sintax error in row {p.lineno}, column {col}: unexpected token ’{p.value}’.")
    else:
        errors.append("Sintax error at the end of the file")

parser = yacc.yacc()
result = parser.parse(data, lexer=lexer)

def print_ast(node, level=0):
    indent = "-" * level
    if isinstance(node, tuple):
        print(f"{indent}{node[0]}")
        for child in node[1:]:
            print_ast(child, level + 1)
    else:
        print(f"{indent}{node}")

if errors:
    for e in errors:
        print(e)
else:
    print_ast(result)