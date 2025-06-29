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

class Scope:
    def __init__(self, parent=None, name="global"):
        self.parent = parent
        self.symbols = {}
        self.name = name
        self.children = []

    def declare(self, name, tipo):
        if name in self.symbols:
            return False
        else:
            self.symbols[name] = tipo
            return True

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return None

    def add_child(self, child_scope):
        self.children.append(child_scope)


def imprimir_tabla(scope, nivel=0):
    indent = "-" * nivel
    for var, tipo in scope.symbols.items():
        
        if(tipo[0] == "function"):
            print(f"{indent}variable: {var} | type: function[..{int(tipo[-1]) - 1}]")
        else:
            print(f"{indent}variable: {var} | type: {tipo}")
            
    # for child in scope.children:
    #     imprimir_tabla(child, nivel + 1)

# These variables keep control over the context 
global_scope = Scope()
current_scope = global_scope
block_counter = 0

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

symbol_table = {}

# precedence is a special object of yacc parser which is used to
# determine what operation goes first, besides that, it also determines
# operators' associativity direction
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
    '''program : open_block declaration_list TkSemicolon statement_list TkCBlock
                | open_block statement_list TkCBlock'''

    global block_counter, current_scope

    if len(p) == 6:
        p[0] = ("Block", ("Symbols Table", current_scope), p[4])
    else:
        p[0] = ("Block", p[2])

    if block_counter != 1:
        current_scope = current_scope.parent


def p_open_block(p):
    '''open_block : TkOBlock'''
    global block_counter, current_scope

    if block_counter != 0:
        new_scope = Scope(parent=current_scope, name=f"block {block_counter}")
        current_scope.add_child(new_scope)
        current_scope = new_scope
    
    block_counter += 1


def p_declaration_list(p):
    '''declaration_list : declaration_list TkSemicolon declaration
                        | declaration'''
    # if len(p) == 4:
    #     p[0] = ('Sequencing', p[1], p[3])
    # else:
    #     p[0] = p[1]   


def p_declaration(p):
    '''declaration : TkInt variable_list
                    | TkBool variable_list'''

    tipo = p[1]
    variables_list = p[2].split(', ')
    for var in variables_list:
        if not(current_scope.declare(var, tipo)):
            errors.append(f"Already declared token ’{var}’.")
            
    # if p[1] == 'int':
    #     p[0] = (p[2] + ': int', p[1])
    # else:
    #     p[0] = (p[2] + ': bool', p[1])


def p_declaration_function(p):
    '''declaration : TkFunction TkOBracket TkSoForth TkNum TkCBracket variable_list'''

    tipo = (p[1], int(p[4]) + 1)
    
    variables_list = p[6].split(', ')
    for var in variables_list:
        if not(current_scope.declare(var, tipo)):
            errors.append(f"Already declared token ’{var}’.")

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
    
    expression_type = p[3][-1]
    var_type = current_scope.lookup(p[1])

    if(var_type and var_type != expression_type):
        errors.append(f"Type error. Variable '{p[1]}' has different type than expression at line {p.lineno(1)} and column {find_column(data, p.slice[1])} ")
    elif(not(var_type)):
        errors.append(f"Error: '{p[1]}' non declared")
    

    p[0] = ("Asig", ("Ident", p[1], expression_type), p[3])


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
    p[0] = ('Concat', p[1], p[3], "String")

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
    if p[1][0] == "Comma":

        if p[3][-1] != "int":
            errors.append(f"Error: Can't accept non integers values in function declaration")
        p[0] = ("Comma", p[1], p[3], ("function", p[1][-1][1] + 1))

    else:
        p[0] = ("Comma", p[1], p[3], ("function", 2))


# Todo: Simplify this
def p_expression_binop(p):
    '''expression : expression TkPlus expression
                    | expression TkMinus expression
                    | expression TkMult expression
                    | expression TkAnd expression
                    | expression TkOr expression
                    | expression TkEqual expression
                    | expression TkNEqual expression
                    | expression TkLess expression
                    | expression TkGreater expression
                    | expression TkLeq expression
                    | expression TkGeq expression'''
    
    left_type = p[1][-1]
    right_type = p[3][-1]
    
    if(p[2]=='+'):
    
        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '+' between non integers operands.")
            p[0] = ('Plus', p[1], p[3], 'error')
        else:
            p[0] = ('Plus', p[1], p[3], 'int')

    elif(p[2]=='*'):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '*' between non integers operands.")
            p[0] = ('Mult', p[1], p[3], 'error')
        else:
            p[0] = ('Mult', p[1], p[3], 'int')

    elif(p[2]=='-'):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '-' between non integers operands.")
            p[0] = ('Minus', p[1], p[3],'error')
        else:
            p[0] = ('Minus', p[1], p[3], 'int')
        
    elif(p[2]=='=='):

        if left_type == 'int' and right_type == 'int':
            p[0] = ('Equal', p[1], p[3], 'bool')
        elif left_type == 'bool' and right_type == 'bool':
            p[0] = ('Equal', p[1], p[3], 'bool')
        else:
            errors.append(f"Can't use '==' between non compatible operands.")
            p[0] = ('Equal', p[1], p[3],'error')
        
    elif(p[2]=='<>'):

        if left_type == 'int' and right_type == 'int':
            p[0] = ('NotEqual', p[1], p[3], 'bool')
        elif left_type == 'bool' and right_type == 'bool':
            p[0] = ('NotEqual', p[1], p[3], 'bool')
        else:
            errors.append(f"Can't use '<>' between non compatible operands.")
            p[0] = ('NotEqual', p[1], p[3],'error')
        
    elif(p[2]=='<='):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '<=' between non integers operands.")
            p[0] = ('Leq', p[1], p[3],'error')
        else:
            p[0] = ('Leq', p[1], p[3], 'bool')
        
    elif(p[2]=='<'):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '<' between non integers operands.")
            p[0] = ('Less', p[1], p[3],'error')
        else:
            p[0] = ('Less', p[1], p[3], 'bool')
        
    elif(p[2]=='>='):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '>=' between non integers operands.")
            p[0] = ('Geq', p[1], p[3],'error')
        else:
            p[0] = ('Geq', p[1], p[3], 'bool')
        
    elif(p[2]=='>'):

        if left_type != 'int' or right_type != 'int':
            errors.append(f"Can't use '>' between non integers operands.")
            p[0] = ('Greater', p[1], p[3],'error')
        else:
            p[0] = ('Greater', p[1], p[3], 'bool')

    elif(p[2]=='and'):

        if left_type != 'bool' or right_type != 'bool':
            errors.append(f"Can't use 'and' between non boolean operands.")
            p[0] = ('And', p[1], p[3],'error')
        else:
            p[0] = ('And', p[1], p[3], 'bool')
        
    elif(p[2]=='or'):

        if left_type != 'bool' or right_type != 'bool':
            errors.append(f"Can't use 'or' between non boolean operands.")
            p[0] = ('Or', p[1], p[3],'error')
        else:
            p[0] = ('Or', p[1], p[3], 'bool')


def p_expression_un(p):
    '''expression : TkNot expression
                    | TkMinus expression %prec UMinus'''
    
    var_type = p[2][-1]
    
    if(p[1] == '!'):
        
        if(var_type != 'bool'):
            errors.append(f"Can't use non boolean type in ! unary operator.")
        p[0] = ('Not', p[2], 'bool')

    elif(p[1] == '-'):
        
        if(var_type != 'int'):
            errors.append(f"Can't use non boolean type in ! unary operator.")
        p[0] = ('Minus', p[2], 'int')


def p_expression_app(p):
    '''expression : TkId TkApp expression'''
    
    expression_type = p[3][-1]
    var_type = current_scope.lookup(p[1])

    if(var_type[0] != "function"):
        errors.append(f"Can't use function application in non function type.")

    if(expression_type != "int"):
        errors.append(f"Can't use non integer type in function application.")

    p[0] = ("ReadFunction", ("Ident", p[1], var_type), p[3], "int")


def p_expression_function_app(p):
    '''expression : function_mod TkApp expression'''

    expression_type = p[3][-1]
    if(expression_type != "int"):
        errors.append(f"Can't use non integer type in function application.")

    p[0] = ("ReadFunction", p[1], p[3])


def p_function_mod(p):
    '''function_mod : function_mod TkOpenPar two_points TkClosePar'''
    
    p[0] = ("WriteFunction", p[1], p[3], p[1][-1])


def p_function_mod_base(p):
    '''function_mod : TkId TkOpenPar two_points TkClosePar'''

    var_type = current_scope.lookup(p[1])

    if(not var_type):
        errors.append(f"Non declare variable.")
    else:
        if(var_type[0] != "function"):
            errors.append(f"Can't use function modification in non function type.")

    p[0] = ("WriteFunction", ("Ident", p[1], var_type), p[3], var_type)


def p_two_points(p):
    '''two_points : expression TkTwoPoints expression'''

    left_expression_type = p[1][-1]
    right_expression_type = p[3][-1]

    if(left_expression_type != "int" or right_expression_type != "int"):
        errors.append(f"Can't use non integer type in function modification.")

    p[0] = ("TwoPoints", p[1], p[3])


def p_expression_num(p):
    '''expression : TkNum'''
    p[0] = ('Literal', p[1], "int")


def p_expression_id(p):
    '''expression : TkId'''

    if(not(current_scope.lookup(p[1]))):
        errors.append(f"Variable non declare at line {p.lineno(1)} and column {find_column(data, p.slice[1])}.")
        p[0] = ('Ident', p[1], 'error')
    else:
        type = current_scope.lookup(p[1])
        p[0] = ('Ident', p[1], type)

def p_expression_parens(p):
    '''expression : TkOpenPar expression TkClosePar'''
    p[0] = p[2]

def p_expression_def(p):
    '''expression : TkTrue
                    | TkFalse'''
    p[0] = ('Literal', p[1], 'bool')

# Function to calculate new line
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

expressions = ["Plus", "Minus", "Mult", "Equal", "NotEqual", "Leq", "Less", "Geq", "Greater", "And", "Or", "Not", "UMinus", "ReadFunction", "WriteFunction", "Concat"]

# This function gets the result tree from yacc parser
# and returns tree in format required
def print_ast(node, level=0):
    indent = "-" * level
    if isinstance(node, tuple):
        
        if node[0] == "Symbols Table":

            print(f"{indent}{node[0]}")
            imprimir_tabla(node[1], level + 1)

        elif node[0] == "Literal":
            print(f"{indent}Literal: {node[1]} | type: {node[-1]}")

        elif node[0] == "Ident":
            if(node[-1][0] != "function"):
                print(f"{indent}Ident: {node[1]} | type: {node[-1]}")
            else:
                print(f"{indent}Ident: {node[1]} | type: {node[-1][0]}[..{node[-1][1] - 1}]")

        elif node[0] == "Comma":
            print(f"{indent}{node[0]} | type: {node[-1][0]} with length={node[-1][1]}")
            for child in node[1:-1]:
                print_ast(child, level + 1)

        elif node[0] == "Asig":
            print(f"{indent}{node[0]}")
            for child in node[1:]:
                print_ast(child, level + 1)

        elif node[0] in expressions:

            if(node[-1][0] != "function"):
                print(f"{indent}{node[0]} | type: {node[-1]}")
            else:
                print(f"{indent}{node[0]} | type: {node[-1][0]}[..{node[-1][1] - 1}]")

            for child in node[1:-1]:
                print_ast(child, level + 1)

        else:
            print(f"{indent}{node[0]}")
            for child in node[1:]:
                if child != 'int' and child != 'bool':
                    print_ast(child, level + 1)
    else:
        print(f"{indent}{node}")

# In case of errors, we don't print the tree
if errors:
    print(errors[0])
    # for e in errors:
    #     print(e)
else:
    print_ast(result)
    #print(symbol_table)