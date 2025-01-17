from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from computedfields.models import ComputedFieldsAdminModel, active_resolver, ContributingModelsModel
from computedfields.admin import ComputedModelsAdmin, ContributingModelsAdmin
from .models import Foo, Bar, Baz, SelfRef


class TestModels(TestCase):
    def setUp(self):
        active_resolver.load_maps(_force_recreation=True)
        self.foo = Foo.objects.create(name='foo1')
        self.bar = Bar.objects.create(name='bar1', foo=self.foo)
        self.baz = Baz.objects.create(name='baz1', bar=self.bar)

    def test_create(self):
        self.foo.refresh_from_db()
        self.bar.refresh_from_db()
        self.baz.refresh_from_db()
        self.assertEqual(self.foo.bazzes, 'baz1')
        self.assertEqual(self.bar.foo_bar, 'foo1bar1')
        self.assertEqual(self.baz.foo_bar_baz, 'foo1bar1baz1')

    def test_create_baz(self):
        Baz.objects.create(name='baz2', bar=self.bar)
        self.foo.refresh_from_db()
        self.assertEqual(self.foo.bazzes, 'baz1, baz2')

    def test_delete_bar(self):
        self.baz.delete()
        self.foo.refresh_from_db()
        self.bar.refresh_from_db()
        self.assertEqual(self.foo.bazzes, '')
        self.assertEqual(self.bar.foo_bar, 'foo1bar1')


class TestModelClassesForAdmin(TestCase):
    def setUp(self):
        active_resolver.load_maps(_force_recreation=True)
        self.site = AdminSite()
        self.adminobj = ComputedModelsAdmin(ComputedFieldsAdminModel, self.site)
        self.adminobj_contributing = ContributingModelsAdmin(ContributingModelsModel, self.site)
        # NOTE: we have to filter proxy models here
        self.models = set(m for m in active_resolver._computed_models.keys() if not m._meta.proxy)

    def test_models_listed(self):
        models = [obj.model_class() for obj in ComputedFieldsAdminModel.objects.all()]
        self.assertIn(Foo, models)
        self.assertIn(Bar, models)
        self.assertIn(Baz, models)
        self.assertEqual(set(models), self.models)

    def test_run_adminclasses(self):
        for instance in ComputedFieldsAdminModel.objects.all():
            self.adminobj.dependencies(instance)
            self.adminobj.name(instance)
            self.adminobj.computed_fields(instance)
            self.adminobj.local_computed_fields_mro(instance)
            self.adminobj.modelgraph(instance)
            self.adminobj.render_modelgraph({}, instance.pk)
        self.adminobj.get_urls()
        self.adminobj.render_graph({})
        self.adminobj.render_uniongraph({})
        for instance in ContributingModelsModel.objects.all():
            self.adminobj_contributing.fk_fields(instance)
            self.adminobj_contributing.name(instance)

    def test_run_adminclasses_pickledmap(self):
        active_resolver._graph = None
        for instance in ComputedFieldsAdminModel.objects.all():
            self.adminobj.dependencies(instance)
            self.adminobj.name(instance)
            self.adminobj.computed_fields(instance)
            self.adminobj.local_computed_fields_mro(instance)
            self.adminobj.modelgraph(instance)
            self.adminobj.render_modelgraph({}, instance.pk)
        self.adminobj.get_urls()
        self.adminobj.render_graph({})
        self.adminobj.render_uniongraph({})
        for instance in ContributingModelsModel.objects.all():
            self.adminobj_contributing.fk_fields(instance)
            self.adminobj_contributing.name(instance)


from computedfields.models import update_dependent
from time import time


def timer(f):
    s = time()
    r = f()
    print(time() - s)
    return r


def create_instances(n):
    inst = []
    for i in range(n):
        inst.append(SelfRef(name='a', xy=10))
    return inst


class TestBigUpdate(TestCase):
    def setUp(self) -> None:
        print('create 10000 records of SelfRef:')
        _ = timer(lambda : SelfRef.objects.bulk_create(create_instances(10000)))
    
    def test_updatetime(self):
        print('update 10000 records of SelfRef:')
        timer(lambda : update_dependent(SelfRef.objects.all()))
        print('check 10000 records of SelfRef:')
        timer(lambda : update_dependent(SelfRef.objects.all()))
