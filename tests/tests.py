"""Basic tests to make sure the language still works."""
import subprocess
from pathlib import Path
import yaml
import unittest
import os

TMP_FILENAME = 'tmp_test_code.tmp'


def run_code(code: str):
    """Compile and a fragment of pyre source code."""
    with open(TMP_FILENAME, 'w') as f:
        f.write(code)
    subprocess.run(['./pyre.py', TMP_FILENAME])
    assembly_file = Path(TMP_FILENAME).absolute().with_suffix('.asm').as_posix()
    object_file = Path(TMP_FILENAME).absolute().with_suffix('.o').as_posix()
    executable = Path(TMP_FILENAME).absolute().with_suffix('').as_posix()
    completed_process = subprocess.run(executable, capture_output=True)
    output = completed_process.stdout.decode('ascii')

    os.remove(TMP_FILENAME)
    os.remove(assembly_file)
    os.remove(object_file)
    os.remove(executable)

    return output


class TestBaseStructures(unittest.TestCase):
    """Test case for the basic structures."""

    def test_if(self):
        """Test the if structures work."""
        with open('tests/if_tests.yaml', 'r') as f:
            tests = yaml.safe_load(f.read())

        for test_name, test in tests.items():
            code = 'import "std"\n' + test['code']
            expected_output = test['expected']
            output = run_code(code)
            self.assertEqual(output, expected_output, f'Failed test {test_name}')

    def test_while(self):
        """Test the while structures work."""
        with open('tests/while_tests.yaml', 'r') as f:
            tests = yaml.safe_load(f.read())

        for test_name, test in tests.items():
            code = 'import "std"\n' + test['code']
            expected_output = test['expected']
            output = run_code(code)
            self.assertEqual(output, expected_output, f'Failed test {test_name}')


if __name__ == '__main__':
    unittest.main(failfast=True)
