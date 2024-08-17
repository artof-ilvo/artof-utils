from unittest import TestCase
from artof_utils.schemas.implement import Implement


class TestImplementManager(TestCase):

    def test_load_implements(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.implement import implement_manager

        # Act
        implements = implement_manager.implements

        # Assert
        self.assertGreater(len(implements), 0)

    def test_context(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.implement import implement_manager

        # Act
        context = implement_manager.implements[0].context

        # Assert
        for t in context['types']:
            self.assertTrue(type(t) is str)
        self.assertIsNotNone(context)

    def test_get_implement(self):
        from artof_utils.implement import implement_manager
        implement = implement_manager.get_implement('new')
        context = implement.context

        self.assertTrue(context['on_taskmap'])
        self.assertTrue(len(context['sections']) == 0)

    def test_parse_implement(self):
        data = {'name': 'new', 'on_taskmap': False, 'types': ['continuous'], 'sections': [
            {'id': 'P', 'width': 0.25, 'up': 0.1, 'down': 0.1, 'transform': {'T': [0, 0, 0], 'R': [0, 0, 0]}}]}

        implement = Implement(**data)

        self.assertFalse(implement.on_taskmap)
        self.assertTrue(len(implement.sections) > 0)
        self.assertTrue('offset' not in implement.context['sections'][0])
