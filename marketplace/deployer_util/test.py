from dict_util import deep_get

a = {'a': 1, 'b.c': {'a': 3, 'b': 4}}
# d = DictWalker(a)
# print(d['b.a'])

# d['a'] = 100
# print(d['a'])

# del d['b.b.b']
# print(d['b'])

# # d['b.a'] = 101
# print(d['b.a'])

# print(d)
# print(d['b.c'])
# print(d[['b.c', 'a']])

print(a)
print(deep_get(a, 'b.c'))
print(deep_get(a, 'b.c', 'a'))
print(deep_get(a, 'x'))
print(deep_get(a, 'x', 'y'))