from settings import *  # noqa
import os


TEST_DISCOVER_ROOT = os.path.abspath(os.path.join(__file__, '../..'))

# Comment this line for turn on debug on tests
LOGGING = {}
DEBUG = 0
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--verbosity=0',
    '--no-byte-compile',
    '--debug-log=error_test.log',
    # '-l',
    '-s',  # comment this line to use pdb
    # '-x',
    '--nologcapture',
    # '--collect-only'
]

if CI:  # noqa
    NOSE_ARGS += [
        '--with-coverage',
        '--cover-package=application',
        '--with-xunit',
        '--xunit-file=test-report.xml',
        '--cover-xml',
        '--cover-xml-file=coverage.xml'
    ]
