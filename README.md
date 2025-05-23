# CI3725---Parser
We will create a micro parser that will be able to translate code from Imperative Language to Lambda Language

## First Step
- Lexer: It's the module which recognizes valid and invalid tokens, it returns a list of errors, in case there are, or a list of recognized tokens. This step is strictly necessary for the other steps to work.
- Lexer usage: python lexer.py [file]
    - It's necessary for the file to be an .imperat file