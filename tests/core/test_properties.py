from neupy.core.config import Configurable
from neupy.core.properties import *

from base import BaseTestCase


class PropertiesTestCase(BaseTestCase):
    def test_basic_properties(self):
        class A(Configurable):
            int_property = Property(expected_type=int)

        a = A()
        a.int_property = 1
        a.int_property = -10
        with self.assertRaises(TypeError):
            a.int_property = '1'

        class B(Configurable):
            int_property = Property(expected_type=(str, set))

        b = B()
        b.int_property = {1, 2, 3}
        b.int_property = 'hello'
        with self.assertRaises(TypeError):
            b.int_property = [5, 4]

    def test_bounded_properties(self):
        class A(Configurable):
            bounded_property = BoundedProperty(min_size=-1, max_size=1)

        a = A()
        a.bounded_property = 0
        with self.assertRaises(ValueError):
            a.bounded_property = -2

    def test_list_of_types_properties(self):
        class A(Configurable):
            list_of_properties = ListOfTypesProperty(inner_list_type=str,
                                                     count=3)

        a = A()
        a.list_of_properties = ('1', '2', '3')

        with self.assertRaises(TypeError):
            a.list_of_properties = (1, '2', '3')

        with self.assertRaises(ValueError):
            a.list_of_properties = ('1', '2', '3', '4')

    def test_choice_property_from_dict(self):
        class A(Configurable):
            choice = ChoiceProperty(choices={'one': 1, 'two': 2, 'three': 3})

        a = A(choice='three')
        self.assertEqual(a.choice, 3)
        a.choice = 'one'
        self.assertEqual(a.choice, 1)

    def test_choice_property_invalid_values(self):
        class A(Configurable):
            choice = ChoiceProperty(choices={'one': 1, 'two': 2, 'three': 3})

        a = A(choice='three')
        invalid_values = [2, None, "2"]
        for invalid_value in invalid_values:
            with self.assertRaises(ValueError):
                a.choice = invalid_value

    def test_choice_property_from_list(self):
        class A(Configurable):
            choice = ChoiceProperty(choices=['one', 'two', 'three'],
                                    default='two')

        a = A()
        self.assertEqual(a.choice, 'two')
        a.choice = 'three'
        self.assertEqual(a.choice, 'three')
