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

# Scope is the class used for symbols table
class Scope:
    def __init__(self, parent=None, name="global"):
        self.parent = parent 
        self.symbols = {} # Here it'll save all variables declared in this scope
        self.name = name # Created just to visually identify scopes, not used in final version
        self.children = [] # Array of childrens, not used in final version
        self.level = 0

    def declare(self, name, tipo, number):
        if name in self.symbols:
            return False
        else:
            self.symbols[name] = (tipo, number)
            return True

    def lookup(self, name, num = 0):
        if name in self.symbols:
            if num == 0:
                return self.symbols[name][0]
            else:
                return self.symbols[name][1]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return None

    def add_child(self, child_scope):
        self.children.append(child_scope)


def print_symbol_table(scope, nivel=0):
    """
        Prints symbol table with identation.

        ### Parameters:
            * `scope`: Object scope defined before
            * `level`: Identation level

        ### Returns: 
            * `None`: Just prints the symbol table asociated to scope.
    """ 
    indent = "-" * nivel
    for var, tipo in scope.symbols.items():
        
        if(tipo[0] == "function"):
            print(f"{indent}variable: {var} | type: function[..{int(tipo[0][-1]) - 1}]")
        else:
            print(f"{indent}variable: {var} | type: {tipo[0]}")

# The SyntaxError exception from yacc was not working correctly, 
# so we decided to use a designed exception to recognize errors and stop parsing
class ParserException(Exception):
    pass

# These variables keep control over the context 
global_scope = Scope()
current_scope = global_scope
block_counter = 0
number_of_variable = 1


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

# Precedence is a special object of yacc parser which is used to
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
    ('right', 'UMinus'),
)


def p_program(p):
    '''program : open_block declaration_list TkSemicolon statement_list TkCBlock
                | open_block statement_list TkCBlock'''

    global block_counter, current_scope

    if len(p) == 6:
        p[0] = ("Block", ("Symbols Table", current_scope), p[4])
    else:
        p[0] = ("Block", ("Symbols Table"), p[2])

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


def p_declaration(p):
    '''declaration : TkInt variable_list
                    | TkBool variable_list'''

    tipo = p[1]
    variables_list = p[2].split(', ')

    global number_of_variable

    for var in variables_list:
        if not(current_scope.declare(var, tipo, number_of_variable)):
            raise ParserException(f"Variable {var} is already declared in the block at line {p.lineno(1)}")

        number_of_variable += 1


def p_declaration_function(p):
    '''declaration : TkFunction TkOBracket TkSoForth TkNum TkCBracket variable_list'''

    tipo = (p[1], int(p[4]) + 1)
    variables_list = p[6].split(', ')

    global number_of_variable

    for var in variables_list:
        if not(current_scope.declare(var, tipo, number_of_variable)):
            raise ParserException(f"Variable {var} is already declared in the block at line {p.lineno(1)}")

        number_of_variable += 1

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

        if (var_type[0] != "function" or var_type[1] != 1 or expression_type != "int"):

            if (expression_type[0] == 'function' and var_type[0] != 'function'):
                raise ParserException(f"Variable {p[1]} is expected to be a function at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
            
            elif (expression_type[0] == 'function' and var_type[0] == 'function'):
                raise ParserException(f"It is expected a list of length {var_type[1]} at line {p.lineno(2)} and column {find_column(data, p.slice[2]) + 1}")
            
            else:
                raise ParserException(f"Type error. Variable {p[1]} has different type than expression at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")

    elif(not(var_type)):
        raise ParserException(f"Variable {p[1]} not declared at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
    
    p[0] = ("Asig", ("Ident", p[1], var_type), p[3])


def p_statement_if(p):
    '''statement : TkIf if_body TkFi'''
    p[0] = ("If", p[2])


def p_if_body(p):
    '''if_body : if_body TkGuard expression TkArrow statement_list
                | expression TkArrow statement_list'''

    if(len(p) == 6):        
        if (p[3][-1] != "bool"):
            raise ParserException(f"No boolean guard at line {p.lineno(4)} and column {find_column(data, p.slice[4])}")
        
        p[0] = ("Guard", p[1], ("Then", p[3], p[5]))

    else:
        if (p[1][-1] != "bool"):
            raise ParserException(f"No boolean guard at line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        
        p[0] = ("Then", p[1], p[3])


def p_statement_while(p):
    '''statement : TkWhile expression TkArrow statement_list TkEnd'''
    if (p[2][-1] != "bool"):
        raise ParserException(f"No boolean guard at line {p.lineno(3)} and column {find_column(data, p.slice[3])}")
    
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
            raise ParserException(f"There is no integer list at line {p.lineno(2)} and column {find_column(data, p.slice[2]) + 1}")
        p[0] = ("Comma", p[1], p[3], ("function", p[1][-1][1] + 1))

    else:
        p[0] = ("Comma", p[1], p[3], ("function", 2))


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
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        p[0] = ('Plus', p[1], p[3], 'int')

    elif(p[2]=='*'):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        p[0] = ('Mult', p[1], p[3], 'int')

    elif(p[2]=='-'):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        p[0] = ('Minus', p[1], p[3], 'int')
        
    elif(p[2]=='=='):

        if left_type != right_type:
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        
        p[0] = ('Equal', p[1], p[3], 'bool')
        
    elif(p[2]=='<>'):

        if left_type != right_type:
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")

        p[0] = ('NotEqual', p[1], p[3], 'bool')

    elif(p[2]=='<='):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")

        p[0] = ('Leq', p[1], p[3], 'bool')
        
    elif(p[2]=='<'):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")

        p[0] = ('Less', p[1], p[3], 'bool')
        
    elif(p[2]=='>='):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        p[0] = ('Geq', p[1], p[3], 'bool')
        
    elif(p[2]=='>'):

        if left_type != 'int' or right_type != 'int':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")

        p[0] = ('Greater', p[1], p[3], 'bool')

    elif(p[2]=='and'):

        if left_type != 'bool' or right_type != 'bool':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")
        p[0] = ('And', p[1], p[3], 'bool')
        
    elif(p[2]=='or'):

        if left_type != 'bool' or right_type != 'bool':
            raise ParserException(f"Type error in line {p.lineno(2)} and column {find_column(data, p.slice[2])}")

        p[0] = ('Or', p[1], p[3], 'bool')


def p_expression_un(p):
    '''expression : TkNot expression
                    | TkMinus expression %prec UMinus'''
    
    var_type = p[2][-1]
    
    if(p[1] == '!'):
        
        if(var_type != 'bool'):
            raise ParserException(f"Type error in line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
        p[0] = ('Not', p[2], 'bool')

    elif(p[1] == '-'):
        
        if(var_type != 'int'):
            raise ParserException(f"Type error in line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
        p[0] = ('UMinus', p[2], 'int')


def p_expression_app(p):
    '''expression : TkId TkApp expression'''
    
    expression_type = p[3][-1]
    var_type = current_scope.lookup(p[1])

    if not var_type:
        raise ParserException(f"Variable not declared at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
    
    elif(var_type[0] != "function"):
        raise ParserException(f"Error. {p[1]} is not indexable at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")

    elif(expression_type != "int"):
        raise ParserException(f"Error. Not integer index for function at line {p.lineno(2)} and column {find_column(data, p.slice[2]) + 1}")
    p[0] = ("ReadFunction", ("Ident", p[1], var_type), p[3], "int")


def p_expression_function_app(p):
    '''expression : function_mod TkApp expression'''

    expression_type = p[3][-1]
    if(expression_type != "int"):
        raise ParserException(f"Error. Not integer index for function at line {p.lineno(2)} and column {find_column(data, p.slice[2]) + 1}")

    p[0] = ("ReadFunction", p[1], p[3], "int")


def p_function_mod(p):
    '''function_mod : function_mod TkOpenPar two_points TkClosePar'''
    
    p[0] = ("WriteFunction", p[1], p[3], p[1][-1])


def p_function_mod_base(p):
    '''function_mod : TkId TkOpenPar two_points TkClosePar'''

    var_type = current_scope.lookup(p[1])

    if not var_type:
        raise ParserException(f"Variable not declared at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
    else:
        if(var_type[0] != "function"):
            raise ParserException(f"The function modification operator is use in not function variable at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")

    p[0] = ("WriteFunction", ("Ident", p[1], var_type), p[3], var_type)


def p_two_points(p):
    '''two_points : expression TkTwoPoints expression'''
    
    left_expression_type = p[1][-1]
    right_expression_type = p[3][-1]

    if (left_expression_type != "int"):
        raise ParserException(f"Expected expression of type int at line {p.lineno(2)} and column {find_column(data, p.slice[2]) - 1}")
    elif (right_expression_type != "int"):
        raise ParserException(f"Expected expression of type int at line {p.lineno(2)} and column {find_column(data, p.slice[2]) + 1}")

    p[0] = ("TwoPoints", p[1], p[3])


def p_expression_num(p):
    '''expression : TkNum'''
    p[0] = ('Literal', p[1], "int")


def p_expression_id(p):
    '''expression : TkId'''

    if(not current_scope.lookup(p[1])):
        raise ParserException(f"Variable not declared at line {p.lineno(1)} and column {find_column(data, p.slice[1])}")
        
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
        raise ParserException(f"Sintax error in row {p.lineno}, column {col}: unexpected token ’{p.value}’.")
    else:
        raise ParserException("Sintax error at the end of the file")

expressions = ["Plus", "Minus", "Mult", "Equal", "NotEqual", "Leq", "Less", "Geq", "Greater", "And", "Or", "Not", "UMinus", "ReadFunction", "WriteFunction", "Concat"]

expressions_extra = ["ReadFunction", "WriteFunction", "Concat"]


# This function gets the result tree from yacc parser
# and returns tree in format required
def print_ast(node, level=0):
    """
        Prints the YACC tree with format.

        ### Parameters:
            * `node`: Object node defined by YACC, if you want the whole tree you have to pass the initial node
            * `level`: Identation level

        ### Returns: 
            * `None`: Just prints the YACC tree with format.
    """

    indent = "-" * level
    if isinstance(node, tuple):
        
        if node[0] == "Symbols Table":

            print(f"{indent}{node[0]}")
            print_symbol_table(node[1], level + 1)

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


def translate_to_lambda(result):

    global current_scope

    current_scope = global_scope

    print("Z = lambda g:(lambda x:g(lambda v:x(x)(v)))(lambda x:g(lambda v:x(x)(v)))")
    print("true = lambda x:lambda y:x")
    print("false = lambda x:lambda y:y")
    print("nil = lambda x:true")
    print("cons = lambda x:lambda y:lambda f: f(x)(y)")
    print("head = lambda p: p(true)")
    print("tail = lambda p:p(false)")
    print("apply = Z(lambda g:lambda f:lambda x:f if x==nil else (g(f(head(x)))(tail(x))))")
    print("lift_do= lambda exp:lambda f:lambda g: lambda x: g(f(x)) if (exp(x)) else x")
    print("do= lambda exp:lambda f:Z(lift_do(exp)(f))\n")

    text = "(lambda x1:" + lambda_translator(result, "") + ")"
    
    print(f"program = {text}")

    current_scope = global_scope

    iter_xi = ""
    iter_var = ""
    iter_consi = ""
    i = 0
    default_value = 0

    for var, tipo in current_scope.symbols.items():

        iter_xi = "lambda " + var + ":" + iter_xi

        if tipo[0] == 'int':
            default_value = 0
        elif tipo[0] == 'bool':
            default_value = True
        elif tipo[0][0] == 'function':
            default_value = [0] * tipo[0][1]

        if(var):
            if(i == 0):
                iter_consi = "cons(" + str(default_value) + ")(nil)" + iter_consi
                iter_var = iter_var + "'" + var + "':" + var
            else:
                iter_consi = "cons(" + str(default_value) + ")" + "(" + iter_consi + ")"
                iter_var = iter_var + ",'" + var + "':" + var

        i += 1

    print(f"\nresult=program({iter_consi})")
    print("print(apply(" + iter_xi + "{" + iter_var + "})(result))\n")


first_block = 0
first_instruction = 0
last_then = 0
first_comma = 0
in_block = 0


def lambda_translator(node, text, level=0):

    global current_scope
    global first_instruction, first_block, last_then, in_block
    if current_scope != None:
        if(current_scope.level > level):
            current_scope = current_scope.parent
            if current_scope != None:
                print(f"Volviendo a tabla {current_scope.name} en nivel {current_scope.level}")

    indent = "-" * level
    if isinstance(node, tuple):
        
        if node[0] == "Block":
            
            if first_block != 0:

                text = lambda_translator(node[1], text, level + 1)

                iter_scope = node[1][1]
                iter_xi = ""
                iter_xi_temp = ""
                tail_amount = 0
                iter_consi = ""
                tail_text = ""
                tail_parenth = ""
                i = 0
                j = 0

                for var, tipo in iter_scope.symbols.items(): 
                    
                    if i == 0:
                        
                        if tipo[0] == 'int':
                            default_value = 0
                        elif tipo[0] == 'bool':
                            default_value = True
                        elif tipo[0][0] == 'function':
                            default_value = [0] * tipo[0][1]

                        if(j == 0):
                            iter_consi = "cons(" + str(default_value) + ")(x1)" + iter_consi
                        else:
                            iter_consi = "cons(" + str(default_value) + ")" + "(" + iter_consi + ")"

                        tail_text = tail_text + "tail("
                        tail_parenth = tail_parenth + ")"

                        tail_amount += 1
                        j += 1
                
                
                iter_consi = f"({iter_consi})"

                in_block = 1
                text = f"{tail_text}{lambda_translator(node[2], text, level + 1)}{iter_consi}{tail_parenth}"

                print(f"Este es el resultado del bloque: {text}\n")

            else:
                first_block = 1
                for child in node[1:]:
                    if child != 'int' and child != 'bool':
                        text = lambda_translator(child, text, level + 1)


        elif node[0] == "Symbols Table":
            
            current_scope = node[1]
            current_scope.level = level
            # print(f"Tabla {current_scope.name} en nivel {current_scope.level}")
            # print(f"{indent}{node[0]}")
            # print_symbol_table(node[1], level + 1)

        elif node[0] == "Sequencing":
            
            left_inst = lambda_translator(node[1], text, level + 1)
            right_inst = lambda_translator(node[2], text, level + 1)

            text = f"({right_inst})({left_inst})"

        elif node[0] == "Literal":

            if(node[1] == 'true'):
                text = 'True'

            elif(node[1] == 'false'):
                text = 'False'

            else:
                text = node[1]

        elif node[0] == "Ident":

            number = current_scope.lookup(node[1], 1)
            text = "x" + str(number)

        elif node[0] == "Asig":

            asign_text = "apply("
            iter_xi = ""
            iter_consi = ""
            i = 0

            asign_var = node[1][1]
            
            iter_scope = current_scope

            var_counter = 0
            var_counter_temp = 2

            while iter_scope != None:
                
                iter_xi_temp = ""
                iter_consi_temp = ""

                if iter_scope == current_scope:
                    
                    for var, tipo in iter_scope.symbols.items():
                    
                        iter_xi_temp = "lambda x" + str(tipo[1]) + ":" + iter_xi_temp

                        if(var == asign_var):

                            exp_text = lambda_translator(node[2], text, level + 1)

                            if(tipo[0][0] == 'function' and tipo[0][1] == 1):
                                exp_text = "[" + exp_text + "]"

                            if(i == 0 and iter_scope.parent == None):
                                iter_consi_temp = "cons(" + exp_text + ")(nil)" + iter_consi_temp
                                i += 1
                            else:

                                if iter_consi_temp != "":
                                    iter_consi_temp = "cons(" + exp_text + ")" + "(" + iter_consi_temp + ")"
                                else:
                                    iter_consi_temp = "cons(" + exp_text + ")"

                        else:
                            if(i == 0 and iter_scope.parent == None):
                                iter_consi_temp = "cons(x" + str(tipo[1]) + ")(nil)" + iter_consi_temp
                                i += 1
                            else:

                                if iter_consi_temp != "":
                                    iter_consi_temp = "cons(x" + str(tipo[1]) + ")" + "(" + iter_consi_temp + ")"
                                else:
                                    iter_consi_temp = "cons(x" + str(tipo[1]) + ")"
                        
                        var_counter += 1
                else:

                    for var, tipo in iter_scope.symbols.items():
                    
                        iter_xi_temp = "lambda x" + str(tipo[1]) + ":" + iter_xi_temp

                        if(i == 0):
                            iter_consi_temp = "cons(x" + str(tipo[1]) + ")(nil)" + iter_consi_temp
                            i += 1
                        else:

                            if iter_consi_temp != "":
                                iter_consi_temp = "cons(x" + str(tipo[1]) + ")" + "(" + iter_consi_temp + ")"
                            else:
                                iter_consi_temp = "cons(x" + str(tipo[1]) + ")"
                        
                        var_counter += 1
                
                print(f"Este es var counter:{var_counter} y este var_counter_temp:{var_counter_temp}")

                iter_xi = iter_xi + iter_xi_temp

                if iter_consi != "":
                    iter_consi =  iter_consi[:-(var_counter_temp - 1)] + "(" +  iter_consi_temp + ")" + ((var_counter_temp - 1) * ')')
                else:
                    iter_consi =  iter_consi_temp

                print("Este es iter_consi: " + iter_consi)

                iter_scope = iter_scope.parent

                var_counter_temp = var_counter
                var_counter = 0

            if(first_instruction == 0 and in_block == 0):
                first_instruction += 1
                asign_text = "(" + asign_text + iter_xi + " " + iter_consi + ")" + ")" + "(x1)" 
            else:
                asign_text = asign_text + iter_xi + " " + iter_consi + ")"

            text = asign_text

            in_block = 0
            
            
        elif node[0] == "Mult":

            text = f"{lambda_translator(node[1], text, level + 1)}*{lambda_translator(node[2], text, level + 1)}"


        elif node[0] == "Comma":

            global first_comma

            if first_comma == 0:
                first_comma = 1
                text = f"[{lambda_translator(node[1], text, level + 1)},{lambda_translator(node[2], text, level + 1)}]"
            else:
                text = f"{lambda_translator(node[1], text, level + 1)},{lambda_translator(node[2], text, level + 1)}"

            if node[2][0] != "Comma":
                first_comma = 0
            

        elif node[0] == "ReadFunction":

            text = f"{lambda_translator(node[1], text, level + 1)}[{lambda_translator(node[2], text, level + 1)}]"

        elif node[0] == "Plus":

            text = f"{lambda_translator(node[1], text, level + 1)}+{lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "Minus":

            text = f"{lambda_translator(node[1], text, level + 1)}-{lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "UMinus":

            text = f"-{lambda_translator(node[1], text, level + 1)}"

        elif node[0] == "Or":

            text = f"{lambda_translator(node[1], text, level + 1)} or {lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "And":

            text = f"{lambda_translator(node[1], text, level + 1)} and {lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "Equal":

            text = f"{lambda_translator(node[1], text, level + 1)} == {lambda_translator(node[2], text, level + 1)}"


        elif node[0] == "NotEqual": 
            
            text = f"{lambda_translator(node[1], text, level + 1)} != {lambda_translator(node[2], text, level + 1)}"
        
        elif node[0] == "Leq":
        
            text = f"{lambda_translator(node[1], text, level + 1)} <= {lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "Less":
        
            text = f"{lambda_translator(node[1], text, level + 1)} < {lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "Geq":
        
            text = f"{lambda_translator(node[1], text, level + 1)} >= {lambda_translator(node[2], text, level + 1)}"
        
        elif node[0] == "Greater":

            text = f"{lambda_translator(node[1], text, level + 1)} > {lambda_translator(node[2], text, level + 1)}"

        elif node[0] == "Not":

            text = f"not({lambda_translator(node[1], text, level + 1)})"

        elif node[0] in expressions_extra:

            for child in node[1:-1]:
                text = lambda_translator(child, text, level + 1)

        elif node[0] == "If":
            
            last_then = 0

            if first_instruction == 0:
                first_instruction += 1

                if (node[1][0] == "Then"):
                    text = f"(lambda x1: {lambda_translator(node[1], text, level + 1)} else (x1))(x1)"
                else:
                    text = f"(lambda x1: {lambda_translator(node[1], text, level + 1)})(x1)"

            else:
                
                if (node[1][0] == "Then"):
                    text = f"(lambda x1: {lambda_translator(node[1], text, level + 1)} else (x1))"
                else:
                    text = f"(lambda x1: {lambda_translator(node[1], text, level + 1)})"
                

        elif node[0] == "Guard":
            
            f_last_then = last_then
            if (last_then == 0):
                last_then = 1
            
            guard_right = lambda_translator(node[2], text, level + 1)
            guard_left = lambda_translator(node[1], text, level + 1)

            if (node[2][0] == "Then" and f_last_then == 0):
                text = f"{guard_left} else ({guard_right} else (x1))"

            elif (node[2][0] == "Then" and f_last_then != 0):
                text = f"{guard_left} else {guard_right}"

            else:
                text = f"{guard_left} else ({guard_right})"
        
        elif node[0] == "Then":

            iter_xi = ""
            i = 0

            for var, tipo in current_scope.symbols.items():
                
                iter_xi = "lambda x" + str(tipo[1]) + ":" + iter_xi

            text = f"({lambda_translator(node[2], text, level + 1)})(x1) if (apply ({iter_xi} {lambda_translator(node[1], text, level + 1)}))(x1)"

        else:

            for child in node[1:]:
                if child != 'int' and child != 'bool':
                    text = lambda_translator(child, text, level + 1) + text

    else:
        print(f"{indent}{node}")
    
    return str(text)

try:
    parser = yacc.yacc()
    result = parser.parse(data, lexer=lexer)

    current_scope = global_scope

    translate_to_lambda(result)

    #print(result)


except ParserException as e:
    print(f"{e}")