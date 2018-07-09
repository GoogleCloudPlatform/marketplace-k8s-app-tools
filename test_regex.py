# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility

import re

# regex = r"{{ \.Values.(.*?) }}"

# test_str = "{{ .Values.imageNginx.image }}"

regex = r"a "

test_str = "a a "

matches = re.search(regex, test_str)

if matches:
    print ("Match was found at {start}-{end}: '{match}'".format(start = matches.start(), end = matches.end(), match = matches.group()))
    
    for groupNum in range(0, len(matches.groups())):
        groupNum = groupNum + 1
        
        print ("Group {groupNum} found at {start}-{end}: {group}".format(groupNum = groupNum, start = matches.start(groupNum), end = matches.end(groupNum), group = matches.group(groupNum)))

# Note: for Python 2.7 compatibility, use ur"" to prefix the regex and u"" to prefix the test string and substitution.