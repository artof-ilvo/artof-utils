from unittest import TestCase
import artof_utils.helpers.task as task


class TestState(TestCase):

    def test_get_hitch_choices(self):
        expected_hitches = {'FF', 'FB', 'RB'}
        hitch_choices = set([choice[0] for choice in task.get_hitch_choices()])
        self.assertEqual(hitch_choices, expected_hitches)

    def test_get_type_choices(self):
        expected_type_choices = {'hitch', 'continuous', 'discrete', 'cardan', 'intermittent'}
        type_choices = set([choice[0] for choice in task.get_type_choices()])
        self.assertEqual(type_choices, expected_type_choices)

    def test_get_implement_choices(self):
        expected_implement_choices = {'none', 'penetrometer', 'active-tool', 'auto-label', 'brander', 'spray-boom'}
        implement_choices = set([choice[0] for choice in task.get_implement_choices()])
        self.assertEqual(implement_choices, expected_implement_choices)
