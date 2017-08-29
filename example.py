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

