'''
# NGLessPy: NGLess as a Python Embedded Language

This is a variation of [NGLess](http://ngless.embl.de) as an embedded language
in Python, thus enabling processing of next generation data through a Python
API.

## Example

```python
    from ngless import NGLess

    sc = NGLess.NGLess('0.6')

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


    ngless '0.6'
    import "mocat" version "0.0"
    
    sample = load_mocat_sample("testing")
    sample = preprocess(sample) using |r|:
        r = substrim(r, min_quality=25)
    
    mapped = map(sample, reference='hg19')

    write(mapped, ofile='ofile.sam')
'''


import os

class NGLessExpression(object):
    def generate(self, indent=''):
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

    def generate(self, indent=''):
        return self.name


class NGLessKeyword(NGLessExpression):
    def __init__(self, keyword):
        self.keyword = keyword

    def generate(self, indent=''):
        return indent + self.keyword


class IFExpression(NGLessExpression):
    '''Represents an if expression'''
    def __init__(self, cond, ifTrue, ifFalse):
        self.cond = cond
        self.ifTrue = ifTrue
        self.ifFalse = ifFalse

    def generate(self, indent=''):
        else_clause = ''
        if self.ifFalse is not None:
            else_clause = (indent + 'else:\n' + self.ifFalse.generate(indent='    ' + indent))
        return (indent + 'if ' + encode_value(self.cond) + ':\n' +
                self.ifTrue.generate(indent=indent+'    ') +
                else_clause)

class ExpressionList(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def generate(self, indent=''):
        return '\n'.join([e.generate(indent) for e in self.exprs])

class Block(object):
    def __init__(self, bvar, block):
        self.bvar = bvar
        self.block = block

    def generate(self, indent=''):
        c = ' using |{}|:\n'.format(self.bvar.name)
        for e in self.block:
            e = e.generate(indent='    ')
            c += e + '\n'
        return c

class Literal(NGLessValue):
    def __init__(self, val):
        self.val = val

    def generate(self, indent=''):
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

    def generate(self, indent=''):
        block_code = ''
        if self.block is not None:
            block_code = self.block.generate(indent=indent)
        return indent + "{}({}{}){}".format(self.fname, self.arg.generate(), encode_kwargs(self.kwargs), block_code)

class PairedCalled(NGLessValue):
    def __init__(self, arg1, arg2, kwargs, block):
        if isinstance(arg1, str) or isinstance(arg2, int):
            arg1 = Literal(arg1)
        if isinstance(arg2, str) or isinstance(arg2, int):
            arg2 = Literal(arg2)
        self.arg1 = arg1
        self.arg2 = arg2
        self.kwargs = kwargs
        self.block = block

    def generate(self, indent=''):
        block_code = ''
        if self.block is not None:
            block_code = self.block.generate(indent)
        return indent + "paired({}, {} {}){}".format(self.arg1.generate(), self.arg2.generate(), encode_kwargs(self.kwargs), block_code)

class BinaryOp(NGLessValue):
    def __init__(self, op, right, left):
        self.op = op
        self.right = right
        self.left = left

    def generate(self, indent=''):
        return encode_value(self.right) + ' ' + self.op + ' ' + encode_value(self.left)

class Assignment(object):
    def __init__(self, var, e):
        self.var = var
        self.expression = e

    def generate(self, indent=''):
        return indent + '{} = {}'.format(self.var.name, self.expression.generate())

class NGLessEnvironment(object):
    def __init__(self, orig):
        self._nglenv__orig = orig
        self._nglenv__vars = {}

    def __getattr__(self, name):
        return self._nglenv__vars[name]

    def _nglenv__create_var(self, name):
        e = NGLessVariable(name)
        self._nglenv__vars[name] = e
        return e

    def __setattr__(self, name, val):
        if name == '_nglenv__vars' or name == '_nglenv__orig':
            object.__setattr__(self, name, val)
        else:
            if name not in self._nglenv__vars:
                self._nglenv__create_var(name)
            self._nglenv__orig.assign(self._nglenv__vars[name], val)

class FunctionCallWithBlock(object):
    def __init__(self, orig, fname, arg, kwargs):
        self.orig = orig
        self.fname = fname
        self.arg = arg
        self.kwargs = kwargs
        self.block_code = []

    def using(self, name):
        def block(f):
            env = NGLessEnvironment(self)
            e = env._nglenv__create_var(name)
            # Some surgery to redirect expressions to the block before calling
            # the inner function:
            orig_script = self.orig.script
            self.orig.script = self.block_code
            f(env)
            self.orig.script = orig_script
            self.orig.add_expression(
                    Assignment(
                        self.arg,
                        FunctionCall(
                            self.fname,
                            self.arg,
                            self.kwargs,
                            Block(e, self.block_code))))

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
        return PairedCalled(sample1, sample2, kwargs, None)


    def if_(self, cond, ifTrue, ifFalse=None):
        self.add_expression(IFExpression(cond, ifTrue, ifFalse))

    discard_ = NGLessKeyword('discard')
    continue_ = NGLessKeyword('continue')

    def preprocess_(self, sample, keep_singles=True, using=None):
        if using is None:
            raise ValueError("Using is missing")
        return FunctionCallWithBlock(self, 'preprocess', sample, {'keep_singles': keep_singles}).using(using)

    def select_(self, arg, **kwargs):
        if kwargs.get('using') is not None:
            return FunctionCallWithBlock(self, 'select', arg, kwargs).using(kwargs.get('using'))
        return FunctionCall('select', arg, kwargs, None)



    def run(self, auto_install=True, verbose=True, ncpus=None, extra_args=[]):
        '''Run the generated script

        Parameters
        ----------
        auto_install : bool, optional (default: True)
            If true, then ngless is installed if not available in the PATH
            (Unix only).

        verbose: bool, optional (default: True)
            Whether to print the resulting script before executing it.

        ncpus : int or str, optional
            How many CPUs to use (corresponds to ngless' -j argument).
            Can be "auto" or an integer.

        extra_args : list of str, optional
            Extra arguments to pass to ngless

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
                cmdline = ['ngless', tfile.name]
                if ncpus:
                    cmdline.extend(['-j', str(ncpus)])
                if extra_args:
                    cmdline.extend(extra_args)
                subprocess.check_call(cmdline)
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

