from tokenize import tokenize
from text import Text
from rules import RuleLoader
from tokens import EOF
from errors import *

import sys

DEBUG = False

class ParseError(CodeTalkerException):
    pass

class TokenStream:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.at = 0

    def current(self):
        if self.at >= len(self.tokens):
            return EOF('')
            raise ParseError('ran out of tokens')
        return self.tokens[self.at]
    
    def next(self):
        self.at += 1
        if self.at > len(self.tokens):
            return EOF('')
            raise ParseError('ran out of tokens')
    advance = next

    def hasNext(self):
        return self.at < len(self.tokens) - 1

class ParseTree(object):
    def __init__(self, name):
        self.children = []

    def add(self, child):
        self.children.append(child)

class Logger:
    def __init__(self, output=True):
        self.indent = 0
        self.output = output
        self.text = ''

    def quite(self):
        self.output = False

    def loud(self):
        self.output = True

    def write(self, text):
        text = ' '*self.indent + text
        if self.output:
            sys.stdout.write(text)
        self.text += text

logger = Logger(DEBUG)

class Grammar:
    def __init__(self, start, tokens, ignore=[]):
        self.start = start
        self.tokens = tokens
        self.ignore = ignore
        self.load_grammar()

    def load_grammar(self):
        self.rules = []
        self.rule_dict = {}
        self.rule_names = []
        self.real_rules = []
        self.load_func(self.start)
        print>>logger, self.rule_names
        print>>logger, self.rules

    def load_func(self, func):
        if func in self.rule_dict:
            return self.rule_dict[func]
        num = len(self.rules)
        self.rule_dict[func] = num
        rule = RuleLoader(self)
        self.rules.append(rule.options)
        name = getattr(func, 'astName', func.__name__)
        self.rule_names.append(name)
        self.real_rules.append(rule)
        func(rule)
        return num

    def get_tokens(self, text):
        return TokenStream(tokenize(self.tokens, text))

    def process(self, text, debug = False):
        logger.output = debug
        text = Text(text)
        tokens = self.get_tokens(text)
        tree = self.parse_rule(0, tokens)
        if tokens.hasNext():
            raise ParseError("not everything was parsed: '%s' left" % (''.join(tok.value for tok in tokens.tokens[tokens.at:])))
        if tree == None:
            raise ParseError('failed to parse')
        return tree

    def parse_rule(self, rule, tokens):
        if rule < 0 or rule >= len(self.rules):
            raise ParseError('invalid rule: %d' % rule)
        print>>logger, 'parsing for rule', self.rule_names[rule]
        logger.indent += 1
        node = ParseTree(self.rule_names[rule])
        for option in self.rules[rule]:
            res = self.parse_children(option, tokens)
            if res is not None:
                print>>logger, 'yes!',self.rule_names[rule], res
                logger.indent -= 1
                node.children = res
                return node
        print>>logger, 'failed', self.rule_names[rule]
        logger.indent -= 1
        return None
    
    def parse_children(self, children, tokens):
        i = 0
        res = []
        while i < len(children):
            while tokens.current().__class__ in self.ignore:
                res.append(tokens.current())
                tokens.advance()
            current = children[i]
            print>>logger, 'parsing child',current,i
            if type(current) == int:
                if current < 0:
                    if isinstance(tokens.current(), self.tokens[-(current + 1)]):
                        res.append(tokens.current())
                        tokens.advance()
                        i += 1
                        continue
                    else:
                        print>>logger, 'token mismatch', tokens.current(), self.tokens[-(current + 1)]
                        return None
                else:
                    sres = self.parse_rule(current, tokens)
                    if sres is None:
                        return None
                    res.append(sres)
                    i += 1
                    continue
            elif type(current) == str:
                if current == tokens.current().value:
                    res.append(tokens.current())
                    tokens.advance()
                    i += 1
                    continue
                print>>logger, 'FAIL string compare:', [current, tokens.current().value]
                return None
            elif type(current) == tuple:
                st = current[0]
                if st == '*':
                    print>>logger, 'star repeat'
                    while 1:
                        print>>logger, 'trying one'
                        at = tokens.at
                        sres = self.parse_children(current[1:], tokens)
                        if sres:
                            print>>logger, 'yes! (star)'
                            res += sres
                        else:
                            print>>logger, 'no (star)'
                            tokens.at = at
                            break
                    i += 1
                    continue
                elif st == '+':
                    at = tokens.at
                    sres = self.parse_children(current[1:], tokens)
                    if sres is not None:
                        res += sres
                    else:
                        return None
                    while 1:
                        at = tokens.at
                        sres = self.parse_children(current[1:], tokens)
                        if sres:
                            res += sres
                        else:
                            tokens.at = at
                            break
                    i += 1
                    continue
                elif st == '|':
                    at = tokens.at
                    for item in current[1:]:
                        if type(item) != tuple:
                            item = (item,)
                        sres = self.parse_children(item, tokens)
                        if sres:
                            res += sres
                            break
                        else:
                            tokens.at = at
                    else:
                        return None
                    i += 1
                    continue
                else:
                    raise ParseError('invalid special token: %s' % st)
            return None
        return res


# vim: et sw=4 sts=4
