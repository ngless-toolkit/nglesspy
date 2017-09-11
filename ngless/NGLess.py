import os

class NGLessVariable(object):
    def __init__(self, name):
        self.name = name

    def generate(self):
        return self.name


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
            c += '    ' + e.generate()
        return c

class Literal(object):
    def __init__(self, val):
        self.val = val

    def generate(self):
        return encode_value(self.val)

def encode_kwargs(kwargs):
    if not kwargs: return ''
    return ', ' + ', '.join(['{}={}'.format(k, encode_value(v)) for k,v in kwargs.items()])

def encode_value(val):
    if isinstance(val, str):
        if val[0] == '{' and val[-1] == '}':
            return val
        return '"{}"'.format(val)
    if isinstance(val, list):
        blocks = [encode_value(v) for v in val]
        return '[' + ', '.join(blocks) + ']'
    return str(val)


class FunctionCall(object):
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

class Assignment(object):
    def __init__(self, var, e):
        self.var = var
        self.expression = e

    def generate(self):
        return '{} = {}'.format(self.var.name, self.expression.generate())

class NGLessEnvironment(object):
    def __init__(self, orig):
        self.orig = orig
        self.vars = {}

    def __getattr__(self, name):
        if name not in self.vars:
            self.vars[name] = NGLessVariable(name)
        return self.vars[name]

    def __setattr__(self, name, val):
        if name == 'vars' or name == 'orig':
            object.__setattr__(self, name, val)
        else:
            self.orig.assign(self.__getattr__(name), val)

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
            f(env)
            self.orig.add_expression(FunctionCall('preprocess', self.sample, {'keep_singles' : self.keep_singles}, Block(r, self.block_code)))
        return block

    def add_expression(self, e):
        self.block_code.append(e)

    def assign(self, var, expr):
        self.add_expression(Assignment(var, expr))


def is_pure(fname):
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

    def preprocess_(self, sample, keep_singles=True, using=None):
        if using is None:
            raise ValueError("Using is missing")
        return PreprocessCall(self, sample, keep_singles).using(using)

    def run(self, auto_install=True, verbose=True):
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
            def make_call(arg, **kwargs):
                return self.function_call(name[:-1], arg, **kwargs)
            return make_call
        raise AttributeError('Unknown attribute')

    def function_call(self, fname, arg, **kwargs):
        e = FunctionCall(fname, arg, kwargs, None)
        if not is_pure(fname):
            self.add_expression(e)
        return e

