"""Tests for dict_util."""

import dict_util
import unittest


class DictUtilTest(unittest.TestCase):

  def test_deep_get(self):
    c = {'c': 1}
    b = {'b': c}
    a = {'a': b}
    self.assertEqual(dict_util.deep_get(a, 'a'), b)
    self.assertEqual(dict_util.deep_get(a, 'a', 'b'), c)
    self.assertEqual(dict_util.deep_get(a, 'a', 'b', 'c'), 1)
    self.assertEqual(dict_util.deep_get(a, 'b'), None)
    self.assertEqual(dict_util.deep_get(a, 'a', 'c'), None)
    self.assertEqual(dict_util.deep_get(a, 'a', 'b', 'd'), None)
