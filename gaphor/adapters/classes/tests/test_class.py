"""
Classes related adapter connection tests.
"""

from gaphor.tests import TestCase
from zope import component
from gaphor import UML
from gaphor.diagram import items
from gaphor.diagram.interfaces import IConnect

class DependencyTestCase(TestCase):

    def test_dependency_glue(self):
        """Test dependency glue to two actor items
        """
        actor1 = self.create(items.ActorItem, UML.Actor)
        actor2 = self.create(items.ActorItem, UML.Actor)
        dep = self.create(items.DependencyItem)

        glued = self.glue(dep, dep.head, actor1)
        self.assertTrue(glued)

        self.connect(dep, dep.head, actor1)

        glued = self.glue(dep, dep.tail, actor2)
        self.assertTrue(glued)


    def test_dependency_connect(self):
        """Test dependency connecting to two actor items
        """
        actor1 = self.create(items.ActorItem, UML.Actor)
        actor2 = self.create(items.ActorItem, UML.Actor)
        dep = self.create(items.DependencyItem)

        self.connect(dep, dep.head, actor1)
        self.connect(dep, dep.tail, actor2)

        self.assertTrue(dep.subject is not None)
        self.assertTrue(isinstance(dep.subject, UML.Dependency))
        self.assertTrue(dep.subject in self.element_factory.select())
        self.assertTrue(dep.head.connected_to is actor1)
        self.assertTrue(dep.tail.connected_to is actor2)

        self.assertTrue(actor1.subject in dep.subject.supplier)
        self.assertTrue(actor2.subject in dep.subject.client)


    def test_dependency_disconnect(self):
        """Test dependency disconnecting using two actor items
        """
        actor1 = self.create(items.ActorItem, UML.Actor)
        actor2 = self.create(items.ActorItem, UML.Actor)
        dep = self.create(items.DependencyItem)

        self.connect(dep, dep.head, actor1)
        self.connect(dep, dep.tail, actor2)

        dep_subj = dep.subject
        self.disconnect(dep, dep.tail)

        self.assertTrue(dep.subject is None)
        self.assertTrue(dep.tail.connected_to is None)
        self.assertTrue(dep_subj not in self.element_factory.select())
        self.assertTrue(dep_subj not in actor1.subject.supplierDependency)
        self.assertTrue(dep_subj not in actor2.subject.clientDependency)


    def test_dependency_reconnect(self):
        """Test dependency reconnection using two actor items
        """
        actor1 = self.create(items.ActorItem, UML.Actor)
        actor2 = self.create(items.ActorItem, UML.Actor)
        dep = self.create(items.DependencyItem)

        self.connect(dep, dep.head, actor1)
        self.connect(dep, dep.tail, actor2)

        dep_subj = dep.subject
        self.disconnect(dep, dep.tail)

        # reconnect
        self.connect(dep, dep.tail, actor2)

        self.assertTrue(dep.subject is not None)
        self.assertTrue(dep.subject is not dep_subj) # the old subject has been deleted
        self.assertTrue(dep.subject in actor1.subject.supplierDependency)
        self.assertTrue(dep.subject in actor2.subject.clientDependency)
        # TODO: test with interface (usage) and component (realization)
        # TODO: test with multiple diagrams (should reuse existing relationships first)


    def test_multi_dependency(self):
        """Test multiple dependencies
        
        Dependency should appear in a new diagram, bound on a new
        dependency item.
        """
        actoritem1 = self.create(items.ActorItem, UML.Actor)
        actoritem2 = self.create(items.ActorItem, UML.Actor)
        actor1 = actoritem1.subject
        actor2 = actoritem2.subject
        dep = self.create(items.DependencyItem)
        
        self.connect(dep, dep.head, actoritem1)
        self.connect(dep, dep.tail, actoritem2)

        self.assertTrue(dep.subject)
        self.assertEquals(1, len(actor1.supplierDependency))
        self.assertTrue(actor1.supplierDependency[0] is dep.subject)
        self.assertEquals(1, len(actor2.clientDependency))
        self.assertTrue(actor2.clientDependency[0] is dep.subject)

        # Do the same thing, but now on a new diagram:

        diagram2 = self.element_factory.create(UML.Diagram)
        actoritem3 = diagram2.create(items.ActorItem, subject=actor1)
        actoritem4 = diagram2.create(items.ActorItem, subject=actor2)
        dep2 = diagram2.create(items.DependencyItem)

        self.connect(dep2, dep2.head, actoritem3)
        self.connect(dep2, dep2.tail, actoritem4)
        self.assertTrue(dep2.subject)
        self.assertEquals(1, len(actor1.supplierDependency))
        self.assertTrue(actor1.supplierDependency[0] is dep.subject)
        self.assertEquals(1, len(actor2.clientDependency))
        self.assertTrue(actor2.clientDependency[0] is dep.subject)

        self.assertTrue(dep.subject is dep2.subject)

# vim:sw=4:et:ai