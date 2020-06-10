"""Tests for bash_util."""

from bash_util import Command, CommandException
import unittest


class BashUtilTest(unittest.TestCase):

  def test_command_success(self):
    cmd = Command('echo Hello')
    self.assertEqual(cmd.output, 'Hello\n')
    self.assertEqual(cmd.exitcode, 0)

  def test_command_success_json(self):
    cmd = Command('echo \'{"string": "mystring", "int": 1, "float": 1.5}\'')
    self.assertEqual(cmd.output,
                     '{"string": "mystring", "int": 1, "float": 1.5}\n')
    self.assertEqual(cmd.exitcode, 0)
    self.assertEqual(cmd.json(), {"string": "mystring", "int": 1, "float": 1.5})

  def test_command_nonzero_exitcode(self):
    with self.assertRaises(CommandException) as context:
      Command('bash -c "exit 1"')
    self.assertEqual(context.exception.exitcode, 1)

  def test_command_failure(self):
    with self.assertRaises(CommandException) as context:
      Command('cat nonexistentfile')
    self.assertEqual(context.exception.exitcode, 1)
    self.assertEqual(
        str(context.exception),
        'cat: nonexistentfile: No such file or directory\n')
