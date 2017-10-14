# NGLessPy: NGLess as a Python Embedded Language

This is a variation of [NGLess](http://ngless.embl.de) as an embedded language
in Python, thus enabling processing of next generation data through a Python
API. See the example below.

[![Build Status](https://travis-ci.org/luispedro/nglesspy.svg?branch=master)](https://travis-ci.org/luispedro/nglesspy)
[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/hyperium/hyper/master/LICENSE)
[![Join the chat at https://gitter.im/luispedro/ngless](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/luispedro/ngless?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This is **very experimental** and can change at any time. Please [get in
touch](mailto:coelho@embl.de) if you want to use it in your work. For
questions, you can also use the [ngless mailing
list](https://groups.google.com/forum/#!forum/ngless).

## Dependencies

- [requests](http://docs.python-requests.org/)
- [NGLess](http://ngless.rtfd.io/)

NGLesspy can auto-install ngless if it needs to.


## Example

Inside the [bin/](https://github.com/luispedro/nglesspy/tree/master/bin)
directory, you will find several simple scripts exposing NGLess functionality
as command line tools. These are also simple examples of how NGLessPy can be
used.

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
    import 'mocat' version '0.0'

    sample = load_mocat_sample('testing')

    preprocess_(sample) using='r':
        r = substrim(r, min_quality=25)

    mapped = map(sample, reference='hg19')
    mapped = select(mapped, keep_if=[{mapped}])

    write(mapped, ofile='ofile.sam')
