'''
# NGLessPy: NGLess as a Python Embedded Language

This is a variation of [NGLess](http://ngless.embl.de) as an embedded language
in Python, thus enabling processing of next generation data through a Python
API.

## Example

```python
    from ngless import NGLess

    sc = NGLess.NGLess('0.0')

    sc.import_('mocat', '0.0')
    e = sc.env

    e.sample = sc.load_mocat_sample_('testing')

    @sc.preprocess_(e.sample, using='r')
    def proc(bk):
        bk.r = sc.substrim_(bk.r, min_quality=25)

    e.mapped = sc.map_(e.sample, reference='hg19')
    e.mapped = sc.select_(e.mapped, keep_if=['{mapped}'])

    sc.write_(e.mapped, ofile='ofile.sam')

    sc.run()
```

This is equivalent to the NGLess script


    ngless '0.0'
    

    

    preprocess_(sample) using='r':
    

    mapped = map(sample, reference='hg19')
    

    write(mapped, ofile='ofile.sam')
'''


import os

class NGLessExpression(object):
    def generate(self):
        raise NotImplementedError("No generate function")

class NGLessValue(NGLessExpression):
    '''Represents a type which can be used for binary operations'''
    def __lt__(self, other):
        return BinaryOp('<', self, other)

    def __le__(self, other):
        return BinaryOp('<=', self, other)

    def __gt__(self, other):
        return BinaryOp('>', self, other)

    def __ge__(self, other):
        return BinaryOp('>=', self, other)

    def __add__(self, other):
        return BinaryOp('+', self, other)

    def __mul__(self, other):
        return BinaryOp('*', self, other)

    def __div__(self, other):
        return BinaryOp('/', self, other)

    def __sub__(self, other):
        return BinaryOp('-', self, other)

class NGLessVariable(NGLessValue):
    '''Variable in NGLess'''
    def __init__(self, name):
        self.name = name

    def generate(self):
        return self.name


class NGLessKeyword(NGLessExpression):
    def __init__(self, keyword):
        self.keyword = keyword

    def generate(self):
        return self.keyword


class IFExpression(NGLessExpression):
    '''Represents an if expression'''
    def __init__(self, cond, ifTrue, ifFalse):
        self.cond = cond
        self.ifTrue = ifTrue
        self.ifFalse = ifFalse

    def generate(self):
        else_clause = ''
        if self.ifFalse is not None:
            else_clause = ['else: ', self.ifFalse.generate()]
        return 'if ' + encode_value(self.cond) + ': ' + self.ifTrue.generate()

class ExpressionList(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def generate(self):
        return [e.generate() for e in self.exprs]

class Block(object):
    def __init__(self, bvar, block):
        self.bvar = bvar
        self.block = block

    def generate(self):
        c = ' using |{}|:\n'.format(self.bvar.name)
        for e in self.block:
            c += '    ' + e.generate() + '\n'
        return c

class Literal(NGLessValue):
    def __init__(self, val):
        self.val = val

    def generate(self):
        return encode_value(self.val)

def encode_kwargs(kwargs):
    if not kwargs: return ''
    return ', ' + ', '.join(['{}={}'.format(k, encode_value(v)) for k,v in kwargs.items()])

def encode_value(val):
    if isinstance(val, NGLessExpression):
        return val.generate()
    if isinstance(val, str):
        if val[0] == '{' and val[-1] == '}':
            return val
        return '"{}"'.format(val)
    if isinstance(val, list):
        blocks = [encode_value(v) for v in val]
        return '[' + ', '.join(blocks) + ']'
    return str(val)


class FunctionCall(NGLessValue):
    def __init__(self, fname, arg, kwargs, block):
        if isinstance(arg, str) or isinstance(arg, int):
            arg = Literal(arg)
        self.fname = fname
        self.arg = arg
        self.kwargs = kwargs
        self.block = block

    def generate(self):
        block_code = ''
        if self.block is not None:
            block_code = self.block.generate()
        return "{}({}{}){}".format(self.fname, self.arg.generate(), encode_kwargs(self.kwargs), block_code)

class BinaryOp(NGLessValue):
    def __init__(self, op, right, left):
        self.op = op
        self.right = right
        self.left = left

    def generate(self):
        return encode_value(self.right) + ' ' + self.op + ' ' + encode_value(self.left)

class Assignment(object):
    def __init__(self, var, e):
        self.var = var
        self.expression = e

    def generate(self):
        return '{} = {}'.format(self.var.name, self.expression.generate())

class NGLessEnvironment(object):
    def __init__(self, orig):
        self._nglenv__orig = orig
        self._nglenv__vars = {}

    def __getattr__(self, name):
        if name not in self._nglenv__vars:
            self._nglenv__vars[name] = NGLessVariable(name)
        return self._nglenv__vars[name]

    def __setattr__(self, name, val):
        if name == '_nglenv__vars' or name == '_nglenv__orig':
            object.__setattr__(self, name, val)
        else:
            self._nglenv__orig.assign(self.__getattr__(name), val)

class PreprocessCall(object):
    def __init__(self, orig, sample, keep_singles):
        self.orig = orig
        self.sample = sample
        self.keep_singles = keep_singles
        self.block_code = []

    def using(self, name):
        def block(f):
            env = NGLessEnvironment(self)
            r = self.orig.generate_variable()
            r.name = name
            # Some surgery to redirect expressions to the block before calling
            # the inner function:
            orig_script = self.orig.script
            self.orig.script = self.block_code
            f(env)
            self.orig.script = orig_script
            self.orig.add_expression(
                    FunctionCall(
                            'preprocess', self.sample,
                            {'keep_singles' : self.keep_singles},
                            Block(r, self.block_code)))

        return block

    def add_expression(self, e):
        self.block_code.append(e)

    def assign(self, var, expr):
        self.add_expression(Assignment(var, expr))


def _is_pure_ngless_function(fname):
    '''Whether the given ngless function is pure (i.e., does not need to be
    assigned to a variable)'''
    return fname not in ["write"]

class NGLess(object):
    def __init__(self, version):
        self.version = version
        self.modules = []
        self.script = []
        self.nextvarix = 0
        self.env = NGLessEnvironment(self)

    def import_(self, modname, modversion):
        self.modules.append((modname, modversion))

    def add_expression(self, exp):
        self.script.append(exp)

    def generate_variable(self):
        n = 'var_{}'.format(self.nextvarix)
        self.nextvarix += 1
        return NGLessVariable(n)

    def paired_(self, sample1, sample2, **kwargs):
        kwargs['second'] = sample2
        return FunctionCall('paired', sample1, kwargs, None)


    def if_(self, cond, ifTrue, ifFalse=None):
        self.add_expression(IFExpression(cond, ifTrue, ifFalse))

    discard_ = NGLessKeyword('discard')
    continue_ = NGLessKeyword('continue')

    def preprocess_(self, sample, keep_singles=True, using=None):
        if using is None:
            raise ValueError("Using is missing")
        return PreprocessCall(self, sample, keep_singles).using(using)

    def run(self, auto_install=True, verbose=True):
        '''Run the generated script

        Parameters
        ----------
        auto_install : bool, optional (default: True)
            If true, then ngless is installed if not available in the PATH
            (Unix only).

        verbose: bool, optional (default: True)
            Whether to print the resulting script before executing it.

        Returns
        -------
        None
        '''
        import tempfile
        import subprocess
        if auto_install:
            from . import install
            install.install_ngless(verbose=verbose)
        with tempfile.NamedTemporaryFile('w+', suffix='.ngl', delete=False) as tfile:
            try:
                tfile.write(self.generate())
                print(self.generate())
                tfile.close()
                subprocess.run(['ngless', tfile.name])
            finally:
                os.unlink(tfile.name)

    def generate(self):
        '''Generate and return NGLess script'''
        from six import StringIO
        out = StringIO()
        out.write('ngless "{}"\n'.format(self.version))
        for (modname,modversion) in self.modules:
            out.write('import "{}" version "{}"\n'.format(modname, modversion))
        out.write("\n")
        for e in self.script:
            out.write(e.generate())
            out.write('\n')
        return out.getvalue()

    def assign(self, var, expr):
        self.add_expression(Assignment(var, expr))

    def __getattr__(self, name):
        if name.endswith('_'):
            return self.function(name[:-1])
        raise AttributeError('Unknown attribute')

    def function(self, fname):
        def make_call(arg, **kwargs):
            return self.function_call(fname, arg, **kwargs)
        return make_call

    def function_call(self, fname, arg, **kwargs):
        e = FunctionCall(fname, arg, kwargs, None)
        if not _is_pure_ngless_function(fname):
            self.add_expression(e)
        return e

