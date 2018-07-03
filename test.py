a = {
  "c": 3,
  "a": 1,
  "b": {
    "c": 2
  }
}

def find(o, key, found=[]):
  if type(o) is dict:
    for k, value in o.iteritems():
      if k == key:
        found.append(value)

      if type(value) is dict:
        find(value, key, found)
  elif type(o) is list:
    for value in o:
      find(value, key, found)

  return found


for i in find(a, "c"):
  print(i)