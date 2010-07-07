#!/usr/bin/env python
import re
from special import star, plus, _or, expand

class Token(object):
    '''Base token class'''
    __slots__ = ('lineno', 'charno', 'value', 'special')
    def __init__(self, value, *more):
        if len(more) == 1 and isinstance(more[0], Text):
            self.lineno = more[0].lineno
            self.charno = more[0].charno
        elif len(more) == 2:
            self.lineno = more[0]
            self.charno = more[1]
        elif not more:
            self.lineno = self.charno = -1
        else:
            raise ValueError('invalid line/char arguments: %s' % (more,))
        self.value = value

    def __repr__(self):
        return u'<%s token "%s" at (%d, %d)>' % (self.__class__.__name__,
                self.value.encode('string_escape'), self.lineno, self.charno)

    def __str__(self):
        return self.value
    
    def __eq__(self, other):
        if type(other) in (tuple, list):
            return tuple(other) == (self.__class__, self.lineno, self.charno, self.value)

    @classmethod
    def check(cls, text):
        '''test to see if a token matches the current text'''
        raise NotImplementedError

class StringToken(Token):
    '''a token that accepts one of many strings'''
    items = []

    @classmethod
    def check(cls, text):
        for item in cls.items:
            if text.current[:len(item)] == item:
                return cls(item, text)

class ReToken(Token):
    '''a token that is based off of a regular expression'''
    rx = None

    @classmethod
    def check(cls, text):
        m = cls.rx.match(text.current)
        if m:
            return cls(m.group(), text)

class SpecialToken(Token):
    '''a special token which is automatically provided by the parser'''
    @classmethod
    def check(cls, text):
        pass

class EOF(SpecialToken):
    '''singleton -- special token for signifying the end of file'''

class INDENT(SpecialToken):
    '''used by the preprocessor to indicate the start of an indented block'''

class DEDENT(SpecialToken):
    '''used by the preprocessor to indicate the end of an indented block'''

class STRING(ReToken):
    rx = re.compile(r'"(?:\\"|[^"])*"|' + r"'(?:\\'|[^'])*'")

class ID(ReToken):
    rx = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')

class NUMBER(ReToken):
    rx = re.compile(r'-?(?:\d+(?:\.\d+)?|\.\d+)')

class WHITE(ReToken):
    rx = re.compile(r'[ \t]+')

class NEWLINE(StringToken):
    # rx = re.compile(r'\n')
    items = ['\n']

class CCOMMENT(ReToken):
    rx = re.compile(r'/\*.*?\*/|//[^\n]*', re.S)

from text import Text
# vim: et sw=4 sts=4
