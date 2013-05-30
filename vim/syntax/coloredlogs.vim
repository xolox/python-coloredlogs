" Vim file type detection script.
" Author: Peter Odding <peter@peterodding.com>
" Last Change: May 30, 2013
" URL: https://pypi.python.org/pypi/coloredlogs

" 2013-05-05 14:31:49 lucid-vm INFO This is the message text.

" Shortcut to define syntax items.
function! s:syntax_match(name, pattern)
  let pattern = printf('/%s/', escape(a:pattern, '/'))
  execute printf('syntax match %s %s', a:name, pattern)
endfunction

" Shortcut to create a 0-width preceding match patterns.
function! s:preceded_by(pattern, preceded_by)
  return '\%(' . a:preceded_by . '\)\@<=' . a:pattern
endfunction

" Re-usable syntax patterns.
let s:date = '^\d\{4}-\d\{2}-\d\{2} \d\{2}:\d\{2}:\d\{2}'
let s:host = s:preceded_by('\S\+', s:date . '\s')
let s:severity_debug = s:preceded_by('DEBUG', s:host . '\s')
let s:severity_debug_or_info = s:preceded_by('DEBUG\|INFO', s:host . '\s')
let s:severity_important = s:preceded_by('WARNING\|ERROR\|CRITICAL', s:host . '\s')

" Syntax items.
call s:syntax_match('myLogsDate', s:date)
call s:syntax_match('myLogsHost', s:host)
call s:syntax_match('myLogsSeverityDebug', s:severity_debug)
call s:syntax_match('myLogsSeverityInfo', s:preceded_by('INFO', s:host . '\s'))
call s:syntax_match('myLogsSeverityImportant', s:severity_important)
call s:syntax_match('myLogsMessageDebug', s:preceded_by('.*', s:severity_debug . '\s'))
call s:syntax_match('myLogsMessageWarning', s:preceded_by('.*', s:severity_important . '\s'))
call s:syntax_match('myLogsDelimiter', s:preceded_by('-\+$', s:severity_debug_or_info . '\s'))

" Default styles.
highlight link myLogsDate Comment
highlight link myLogsHost Special
highlight link myLogsSeverityDebug Operator
highlight link myLogsSeverityInfo Operator
highlight link myLogsSeverityImportant Operator
highlight link myLogsMessageDebug Comment
highlight link myLogsMessageWarning WarningMsg
highlight link myLogsDelimiter Special

" vim: ts=2 sw=2 et
