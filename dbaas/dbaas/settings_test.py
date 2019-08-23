from settings import *  # noqa

# Comment this line for turn on debug on tests
LOGGING = {}
DEBUG = 0
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--verbosity=0',
    '--no-byte-compile',
    '--debug-log=error_test.log',
    '-s',
    '--nologcapture'
]

if CI:
    NOSE_ARGS += [
        '--with-coverage',
        '--cover-package=application',
        '--with-xunit',
        '--xunit-file=test-report.xml',
        '--cover-xml',
        '--cover-xml-file=coverage.xml'
    ]
