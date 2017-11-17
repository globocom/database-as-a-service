from unittest import TestCase
from logical.validators import ParameterValidator
from physical.tests.factory import ParameterFactory 


class IntegerTestCase(TestCase):

	def setUp(self):
		self.parameter = ParameterFactory.build(parameter_type='integer')

	def test_single_integer_acceptable(self):
		self.parameter.allowed_values = '1'
		result = ParameterValidator.validate_value('1', self.parameter)

		self.assertTrue(result)

	def test_single_integer_invalid(self):
		self.parameter.allowed_values = '1'
		result = ParameterValidator.validate_value('1.0', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('d', self.parameter)
		self.assertFalse(result)

	def test_many_integers_acceptable(self):
		self.parameter.allowed_values = '1,2,3'
		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('3', self.parameter)
		self.assertTrue(result)

	def test_many_integers_invalid(self):
		self.parameter.allowed_values = '1,2,3'
		result = ParameterValidator.validate_value('4', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertFalse(result)


	def test_range_integer_acceptable(self):
		self.parameter.allowed_values = '0:2'
		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertTrue(result)

	def test_range_integer_invalid(self):
		self.parameter.allowed_values = '0:2'
		result = ParameterValidator.validate_value('-1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('3', self.parameter)
		self.assertFalse(result)

	def test_unlimited_range_integer_acceptable(self):
		self.parameter.allowed_values = '2:'
		result = ParameterValidator.validate_value('2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('3', self.parameter)
		self.assertTrue(result)

	def test_unlimited_range_integer_invalid(self):
		self.parameter.allowed_values = '2:'
		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertFalse(result)

	def test_mixed_allowed_acceptable(self):
		self.parameter.allowed_values = '0:2,4 ,5 ,7:'

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('4', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('5', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('7', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('8', self.parameter)
		self.assertTrue(result)

	def test_mixed_allowed_invalid(self):
		self.parameter.allowed_values = '0:2,4 ,5 ,7:'

		result = ParameterValidator.validate_value('-1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('3', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('6', self.parameter)
		self.assertFalse(result)

class FloatTestCase(TestCase):

	def setUp(self):
		self.parameter = ParameterFactory.build(parameter_type='float')

	def test_single_float_acceptable(self):
		self.parameter.allowed_values = '1.0'

		result = ParameterValidator.validate_value('1.0', self.parameter)
		self.assertTrue(result)

	def test_single_float_invalid(self):
		self.parameter.allowed_values = '1.0'
		result = ParameterValidator.validate_value('1.3', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('d', self.parameter)
		self.assertFalse(result)

	def test_many_float_acceptable(self):
		self.parameter.allowed_values = '1.1,2.1,3.3'
		result = ParameterValidator.validate_value('1.1', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2.1', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('3.3', self.parameter)
		self.assertTrue(result)

	def test_many_floats_invalid(self):
		self.parameter.allowed_values = '1.1,2.1,3.3'
		result = ParameterValidator.validate_value('1.2', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('3.0', self.parameter)
		self.assertFalse(result)


	def test_range_float_acceptable(self):
		self.parameter.allowed_values = '0.0:2.2'

		result = ParameterValidator.validate_value('0.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('0.3', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2.2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2.1', self.parameter)
		self.assertTrue(result)

	def test_range_float_invalid(self):
		self.parameter.allowed_values = '0.0:2.2'
		result = ParameterValidator.validate_value('-1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('0', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('2.3', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('2.4', self.parameter)
		self.assertFalse(result)

	def test_unlimited_range_float_acceptable(self):
		self.parameter.allowed_values = '2.0:'
		result = ParameterValidator.validate_value('2.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2.3', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('4.0', self.parameter)
		self.assertTrue(result)

	def test_unlimited_range_float_invalid(self):
		self.parameter.allowed_values = '2.0:'
		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('1.9', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('4', self.parameter)
		self.assertFalse(result)

	def test_mixed_allowed_acceptable(self):
		self.parameter.allowed_values = '.25:2.2,4.0 ,5.0 ,7.0:'

		result = ParameterValidator.validate_value('0.5', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('1.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('.25', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('2.2', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('4.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('5.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('7.0', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('7.3', self.parameter)
		self.assertTrue(result)

	def test_mixed_allowed_invalid(self):
		self.parameter.allowed_values = '0:2.2,4.0 ,5.0 ,7.0:'

		result = ParameterValidator.validate_value('-1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('3.9', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('6.9', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('1', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('4', self.parameter)
		self.assertFalse(result)

class StringTestCase(TestCase):
	def setUp(self):
		self.parameter = ParameterFactory.build(parameter_type='string')

	def test_single_string_acceptable(self):
		self.parameter.allowed_values = 'ROW'
		result = ParameterValidator.validate_value('ROW', self.parameter)
		self.assertTrue(result)

		self.parameter.allowed_values = ''
		result = ParameterValidator.validate_value('bla', self.parameter)
		self.assertTrue(result)
		result = ParameterValidator.validate_value('10', self.parameter)
		self.assertTrue(result)

	def test_single_string_invalid(self):
		self.parameter.allowed_values = 'ROW'
		result = ParameterValidator.validate_value('RoW', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('sdfsdf', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('15.2', self.parameter)
		self.assertFalse(result)

	def test_many_strings_acceptable(self):
		self.parameter.allowed_values = 'ROW ,  MIXED,STATEMENT'
		result = ParameterValidator.validate_value('ROW', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('MIXED', self.parameter)
		self.assertTrue(result)

		result = ParameterValidator.validate_value('STATEMENT', self.parameter)
		self.assertTrue(result)

	def test_many_strings_invalid(self):
		self.parameter.allowed_values = 'ROW ,  MIXED,STATEMENT'
		result = ParameterValidator.validate_value('dsfsdfsdf', self.parameter)
		self.assertFalse(result)

		result = ParameterValidator.validate_value('MIXED,STATEMENT', self.parameter)
		self.assertFalse(result)
