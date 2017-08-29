# NGLess as a Python Embedded Language


This is a variation of [NGLess](http://ngless.embl.de) as an embedded language
in Python. See the example below.

This is **very experimental** and can change at any time.  Please [get in
touch](mailto:coelho@embl.de) if you want to use it in your work. For
questions, you can also use the [ngless mailing
list](https://groups.google.com/forum/#!forum/ngless).

## Example

    import NGLess

    sc = NGLess.NGLess('0.0')

    sc.import_('mocat', '0.0')
    e = sc.env

    e.sample = sc('load_mocat_sample', 'testing')

    @sc.preprocess_(e.sample, using='r')
    def proc(bk):
        bk.r = sc('substrim', bk.r, min_quality=25)

    e.mapped = sc('map', e.sample, reference='hg19')
    e.mapped = sc('select', e.mapped, keep_if=['{mapped}'])

    sc('write', e.mapped, ofile='ofile.sam')

    sc.run()


