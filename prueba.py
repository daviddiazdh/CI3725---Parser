Z = lambda g:(lambda x:g(lambda v:x(x)(v)))(lambda x:g(lambda v:x(x)(v)))
true = lambda x:lambda y:x
false = lambda x:lambda y:y
nil = lambda x:true
cons = lambda x:lambda y:lambda f: f(x)(y)
head = lambda p: p(true)
tail = lambda p:p(false)
apply = Z(lambda g:lambda f:lambda x:f if x==nil else (g(f(head(x)))(tail(x))))
lift_do= lambda exp:lambda f:lambda g: lambda x: g(f(x)) if (exp(x)) else x
do= lambda exp:lambda f:Z(lift_do(exp)(f))


program = (lambda x1:tail(tail(apply(lambda x4:lambda x3:lambda x2:lambda x1: cons(x4)(cons(True)(cons(x2)(cons(x1)(nil)))))(cons(True)(cons(True)(x1))))))

result=program(cons(0)(cons(0)(nil)))
print(apply(lambda y:lambda x:{'x':x,'y':y})(result))