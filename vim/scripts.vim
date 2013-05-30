" Vim file type detection script.
" Author: Peter Odding <peter@peterodding.com>
" Last Change: May 30, 2013
" URL: https://pypi.python.org/pypi/coloredlogs

if did_filetype()
  finish
endif

if match(getline(1, 10), '^\d\{4}-\d\{2}-\d\{2} \d\{2}:\d\{2}:\d\{2} \S\+ \(DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL\) ') >= 0
  " Custom logging format emitted by a Python logging handler.
  setfiletype coloredlogs
endif

" vim: ts=2 sw=2 et
