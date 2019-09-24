#!/usr/bin/env python

from nbpages import make_parser, run_parsed, make_html_index

args = make_parser().parse_args()

converted = run_parsed('.', output_type='HTML', args=args)
make_html_index(converted, './index.tpl')
