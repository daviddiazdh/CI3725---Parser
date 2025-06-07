import ply.yacc as yacc
import sys
import re

# Get the token map from the lexer.  This is required.
from lexer import tokens, lexer

lexer.lineno = 1

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

precedence = (
    ('left', 'TkOr'),
    ('left', 'TkAnd'),
    ('left', 'TkEqual', 'TkNEqual'),
    ('nonassoc', 'TkLess', 'TkLeq', 'TkGreater', 'TkGeq'),
    ('left', 'TkPlus', 'TkMinus'),
    ('left', 'TkMult', 'TkDiv'),
    ('nonassoc', 'TkApp'),
    ('right', 'TkNot')
)

def p_program(p):
    '''program : TkOBlock declaration_list TkSemicolon statement_list TkCBlock'''
    p[0] = ["program", p[2] + p[4]]


def p_declaration_list(p):
    '''declaration_list : declaration_list TkSemicolon declaration
                        | declaration'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]] 
    else:
        p[0] = [p[1]]        


def p_declaration(p):
    '''declaration : TkInt variable_list
                   | TkBool variable_list'''
    p[0] = (p[1], p[2]) 

def p_declaration_function(p):
    '''declaration : TkFunction TkOBracket TkSoForth TkNum TkCBracket variable_list'''
    p[0] = (p[1], 'range : 0..' + str(p[4]), p[6])

def p_variable_list(p):
    '''variable_list : variable_list TkComma variable
                     | variable'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_variable(p):
    '''variable : TkId'''
    p[0] = p[1]


def p_statement_list(p):
    '''statement_list : statement_list TkSemicolon statement
                      | statement'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_statement_asig(p):
    '''statement : TkId TkAsig expression
                 | TkId TkAsig bool_expression
                 | TkId TkAsig expression_list
                 | TkId TkAsig function_mod'''
    p[0] = ("assign", p[1], p[3])

def p_statement_if(p):
    '''statement : TkIf if_body TkFi'''
    p[0] = ("if", p[2])

def p_if_body(p):
    '''if_body : bool_expression TkArrow statement_list
                | if_body TkGuard bool_expression TkArrow statement_list'''
    if(len(p) == 4):
        p[0] = ("then", p[1], p[3])
    else:
        p[0] = (p[1], ("then",  p[3], p[5]))

def p_statement_while(p):
    '''statement : TkWhile bool_expression TkArrow statement_list TkEnd'''
    p[0] = ("while", p[2], p[4])

def p_statement_print(p):
    '''statement : TkPrint expression
                | TkPrint bool_expression
                | TkPrint string'''
    p[0] = ("print", p[2])

def p_statement_skip(p):
    '''statement : TkSkip'''
    p[0] = (p[1])

def p_string_binop(p):
    '''string : string TkPlus string
                | string TkPlus expression
                | expression TkPlus string'''
    p[0] = (p[2], p[1], p[3])

def p_string(p):
    '''string : TkString'''
    p[0] = ('string', p[1])

def p_string_parenthesis(p):
    '''string : TkOpenPar TkString TkClosePar'''
    p[0] = ('string', p[2])

def p_statement_program(p):
    '''statement : program'''
    p[0] = p[1]

def p_expression_list(p):
    '''expression_list : expression_list TkComma expression
                        | expression'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]] 

def p_expression_binop(p):
    '''expression : expression TkPlus expression
                | expression TkMinus expression
                | expression TkMult expression'''
    p[0] = (p[2], p[1], p[3])

def p_expression_app(p):
    '''expression : TkId TkApp expression
                | function_mod TkApp expression'''
    p[0] = ("app", p[1], p[3])

def p_function_mod(p):
    '''function_mod : TkId function_mod_list'''
    p[0] = ("write_function", p[1], p[2])

def p_function_mod_list(p):
    '''function_mod_list : function_mod_list TkOpenPar expression TkTwoPoints expression TkClosePar 
                        | TkOpenPar expression TkTwoPoints expression TkClosePar'''
    if(len(p)== 6):
        p[0] = ("two_points", p[2], p[4])
    else:
        p[0] = (p[1], ("two_points", p[3], p[5]))

def p_expression_unop(p):
    '''expression : TkMinus expression'''
    p[0] = (p[1], p[2])

def p_expression_num(p):
    '''expression : TkNum'''
    p[0] = ('num', p[1])

def p_expression_id(p):
    '''expression : TkId'''
    p[0] = ('id', p[1])

def p_expression_parens(p):
    '''expression : TkOpenPar expression TkClosePar'''
    p[0] = p[2]

def p_bool_expression_binop(p):
    '''bool_expression : bool_expression TkAnd bool_expression
                    | bool_expression TkOr bool_expression
                    | bool_expression TkEqual bool_expression
                    | bool_expression TkNEqual bool_expression
                    | TkNot bool_expression
                    | expression TkLess expression
                    | expression TkGreater expression
                    | expression TkLeq expression
                    | expression TkGeq expression
                    | expression TkEqual expression
                    | expression TkNEqual expression
                    '''
    if(p[1] == '!'):
        p[0] = (p[1], p[2])
    else:
        p[0] = (p[2], p[1], p[3])

def p_bool_expression_def(p):
    '''bool_expression : TkTrue
                    | TkFalse'''
    p[0] = ('bool', p[1])

def p_bool_expression_id(p):
    '''bool_expression : TkId'''
    p[0] = ('id', p[1])

def p_bool_expression_parenthesis(p):
    '''bool_expression : TkOpenPar bool_expression TkClosePar'''
    p[0] = (p[2])

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def p_error(p):
    if p:
        print(f"Error de sintaxis en '{p.value}' (línea {p.lineno})")
    else:
        print("Error de sintaxis al final del archivo")

parser = yacc.yacc()
result = parser.parse(data, lexer=lexer)
print(result)