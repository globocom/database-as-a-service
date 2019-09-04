from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.forms.models import inlineformset_factory

from ..forms.engine_patch import EnginePatchFormset, EnginePatchForm
from ..models import Engine, EnginePatch
from . import factory


class EnginePatchFormCreateTest(TestCase):

    def setUp(self):
        self.engine = factory.EngineFactory()
        self.engine_patch_formset = inlineformset_factory(
            Engine,
            EnginePatch,
            form=EnginePatchForm,
            formset=EnginePatchFormset
        )

    def test_valid_data_create(self):
        """Testing creating initial patch with valid data."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test'
        })

        self.assertTrue(formset.is_valid())

    def test_blank_data_create(self):
        """Testing creating initial patch with blank data."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '',
            'patchs-0-is_initial_patch': '',
            'patchs-0-patch_path': ''
        })

        self.assertFalse(formset.is_valid())

    def test_required_data_create(self):
        """Testing creating initial patch with empty patch_version."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test'
        })

        self.assertFalse(formset.is_valid())
        self.assertTrue('patch_version' in str(formset.errors))

    def test_duplicated_initial_version_create(self):
        """Testing creating engine patch with two initial versions."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': True,
            'patchs-1-patch_path': 'test'
        })

        self.assertFalse(formset.is_valid())

    def test_duplicated_initial_version_delete_create(self):
        """Testing creating engine patch with two initial versions, but the
        last one is being deleted."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': True,
            'patchs-1-patch_path': 'test',
            'patchs-1-DELETE': True
        })

        self.assertTrue(formset.is_valid())

    def test_blank_patch_path_initial_patch_true_create(self):
        """Testing creating engine patch with empty patch_path to initial
        version."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': 'test',
            'patchs-1-required_disk_size_gb': 9.5
        })

        self.assertTrue(formset.is_valid())

    def test_blank_required_disk_size_initial_patch_true_create(self):
        """Testing creating engine patch with empty required_disk_size_gb, when
        is_initial_patch equals True."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-0-required_disk_size_gb': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': 'test',
            'patchs-1-required_disk_size_gb': 9.5
        })

        self.assertTrue(formset.is_valid())

    def test_blank_patch_path_initial_patch_false_create(self):
        """Testing creating engine patch with empty patch_path, when
        is_initial_patch equals False."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': ''
        })

        self.assertFalse(formset.is_valid())
        self.assertTrue('patch_path' in str(formset.errors))

    def test_blank_required_disk_size_initial_patch_false_create(self):
        """Testing creating engine patch with empty required_disk_size, when
        is_initial_patch equals False."""
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-0-required_disk_size': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': 'test',
            'patchs-1-required_disk_size': ''
        })

        self.assertFalse(formset.is_valid())
        self.assertTrue('required_disk_size' in str(formset.errors))

    def test_blank_patch_path_initial_patch_false_delete_checked_create(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': '',
            'patchs-1-DELETE': True
        })

        self.assertTrue(formset.is_valid())

    def test_blank_required_disk_size_delete_checked_create(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': 'test',
            'patchs-1-required_disk_size': '',
            'patchs-1-DELETE': True
        })

        self.assertTrue(formset.is_valid())


class EnginePatchFormUpdateTest(TestCase):

    def setUp(self):
        self.engine = factory.EngineFactory()
        self.engine_patch_formset = inlineformset_factory(
            Engine,
            EnginePatch,
            form=EnginePatchForm,
            formset=EnginePatchFormset
        )

    def test_valid_data_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test'
        }, instance=self.engine)

        self.assertTrue(formset.is_valid())

    def test_blank_data_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '',
            'patchs-0-is_initial_patch': '',
            'patchs-0-patch_path': ''
        }, instance=self.engine)

        self.assertFalse(formset.is_valid())

    def test_required_data_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '1',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test'
        }, instance=self.engine)

        self.assertFalse(formset.is_valid())
        self.assertTrue('patch_version' in str(formset.errors))

    def test_duplicated_initial_version_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': True,
            'patchs-1-patch_path': 'test'
        }, instance=self.engine)

        self.assertFalse(formset.is_valid())

    def test_duplicated_initial_version_delete_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': 'test',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': True,
            'patchs-1-patch_path': 'test',
            'patchs-1-DELETE': True
        }, instance=self.engine)

        self.assertTrue(formset.is_valid())

    def test_blank_patch_path_initial_patch_true_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-0-required_disk_size_gb': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': 'test',
            'patchs-1-required_disk_size_gb': 9.5,
        }, instance=self.engine)

        self.assertTrue(formset.is_valid())

    def test_blank_patch_path_initial_patch_false_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': ''
        }, instance=self.engine)

        self.assertFalse(formset.is_valid())
        self.assertTrue('patch_path' in str(formset.errors))

    def test_blank_patch_path_initial_patch_false_delete_checked_update(self):
        formset = self.engine_patch_formset({
            'patchs-INITIAL_FORMS': '0',
            'patchs-TOTAL_FORMS': '2',
            'patchs-MAX_NUM_FORMS': '100',
            'patchs-0-patch_version': '1',
            'patchs-0-is_initial_patch': True,
            'patchs-0-patch_path': '',
            'patchs-1-patch_version': '2',
            'patchs-1-is_initial_patch': False,
            'patchs-1-patch_path': '',
            'patchs-1-DELETE': True
        }, instance=self.engine)

        self.assertTrue(formset.is_valid())
