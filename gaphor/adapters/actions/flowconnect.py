"""
Flow item adapter connections.
"""

from gaphor.adapters.connectors import RelationshipConnect
from zope import interface, component
from gaphor import UML
from gaphor.diagram import items
from gaphor.diagram.interfaces import IConnect


class FlowConnect(RelationshipConnect):
    """
    Connect FlowItem and Action/ObjectNode, initial/final nodes.
    """

    CAN_BE_UNARY = True   # flow can connect same actions

    def glue(self, handle, port):
        line = self.line
        subject = self.element.subject

        if handle is line.head and isinstance(subject, UML.FinalNode) \
           or handle is line.tail and isinstance(subject, UML.InitialNode):
            return None

        return super(FlowConnect, self).glue(handle, port)

    def connect_subject(self, handle):
        line = self.line
        element = self.element
        # TODO: connect opposite side again (in case it's a join/fork or
        #       decision/merge node)
        if isinstance(line.head.connected_to, items.ObjectNodeItem) \
           or isinstance(line.tail.connected_to, items.ObjectNodeItem):
            relation = self.relationship_or_new(UML.ObjectFlow,
                        ('source', 'outgoing'),
                        ('target', 'incoming'))
        else:
            relation = self.relationship_or_new(UML.ControlFlow,
                        ('source', 'outgoing'),
                        ('target', 'incoming'))
        if not relation.guard:
            relation.guard = self.element_factory.create(UML.LiteralSpecification)
        line.subject = relation
        opposite = line.opposite(handle)
        if opposite and isinstance(opposite.connected_to, (items.ForkNodeItem, items.DecisionNodeItem)):
            adapter = component.queryMultiAdapter((opposite.connected_to, line), IConnect)
            adapter.combine_nodes()

    def disconnect_subject(self, handle):
        super(FlowConnect, self).disconnect_subject(handle)
        line = self.line
        opposite = line.opposite(handle)
        if opposite and isinstance(opposite.connected_to, (items.ForkNodeItem, items.DecisionNodeItem)):
            adapter = component.queryMultiAdapter((opposite.connected_to, line), IConnect)
            adapter.decombine_nodes()

component.provideAdapter(factory=FlowConnect,
                         adapts=(items.ActionItem, items.FlowItem))
component.provideAdapter(factory=FlowConnect,
                         adapts=(items.ActivityNodeItem, items.FlowItem))
component.provideAdapter(factory=FlowConnect,
                         adapts=(items.ObjectNodeItem, items.FlowItem))


class FlowForkDecisionNodeConnect(FlowConnect):
    """
    Abstract class with common behaviour for Fork/Join node and
    Decision/Merge node.
    """
    def glue(self, handle, port):
        # No cyclic connect is possible on a Flow/Decision node:
        head, tail = self.line.head, self.line.tail
        subject = self.element.subject
        
        if handle is head and tail.connected_to and tail.connected_to.subject is subject \
           or handle is tail and head.connected_to and head.connected_to.subject is subject:
            return None

        return super(FlowForkDecisionNodeConnect, self).glue(handle, port)

    def combine_nodes(self):
        """
        Combine join/fork or decision/methe nodes into one diagram item.
        """
        fork_node_class = self.fork_node_class
        join_node_class = self.join_node_class
        line = self.line
        element = self.element
        subject = element.subject
        if len(subject.incoming) > 1 and len(subject.outgoing) < 2:
            self.element_factory.swap_element(subject, join_node_class)
            element.request_update()
        elif len(subject.incoming) < 2 and len(subject.outgoing) > 1:
            self.element_factory.swap_element(subject, fork_node_class)
            element.request_update()
        elif not element.combined and len(subject.incoming) > 1 and len(subject.outgoing) > 1:
            join_node = subject

            # determine flow class:
            if [ f for f in join_node.incoming if isinstance(f, UML.ObjectFlow) ]:
                flow_class = UML.ObjectFlow
            else:
                flow_class = UML.ControlFlow
            
            self.element_factory.swap_element(join_node, join_node_class)
            fork_node = self.element_factory.create(fork_node_class)
            for flow in list(join_node.outgoing):
                flow.source = fork_node
            flow = self.element_factory.create(flow_class)
            flow.source = join_node
            flow.target = fork_node

            element.combined = fork_node

    def decombine_nodes(self):
        """
        Decombine join/fork or decision/merge nodes.
        """
        fork_node_class = self.fork_node_class
        join_node_class = self.join_node_class
        line = self.line
        element = self.element
        if element.combined:
            join_node = element.subject
            flow = join_node.outgoing[0]
            fork_node = flow.target
            assert fork_node is element.combined
            assert isinstance(join_node, join_node_class)
            assert isinstance(fork_node, fork_node_class)

            if len(join_node.incoming) < 2 or len(fork_node.outgoing) < 2:
                # Move all outgoing edges to the first node (the join node):
                for flow in list(fork_node.outgoing):
                    flow.source = join_node
                flow.unlink()
                fork_node.unlink()

                # swap subject to fork node if outgoing > 1
                if len(join_node.outgoing) > 1:
                    assert len(join_node.incoming) < 2
                    self.element_factory.swap_element(join_node, fork_node_class)
                element.combined = None

    def connect_subject(self, handle):
        """
        In addition to a subject connect, the subject of the element may 
        be changed.
        For readability, parameters are named afther the classes used by
        Join/Fork nodes.
        """
        super(FlowForkDecisionNodeConnect, self).connect_subject(handle)

        # Switch class for self.element Join/Fork depending on the number
        # of incoming/outgoing edges.
        self.combine_nodes()

    def disconnect_subject(self, handle):
        super(FlowForkDecisionNodeConnect, self).disconnect_subject(handle)
        if self.element.combined:
            self.decombine_nodes()


class FlowForkNodeConnect(FlowForkDecisionNodeConnect):
    """
    Connect Flow to a ForkNode.
    """
    component.adapts(items.ForkNodeItem, items.FlowItem)

    fork_node_class=UML.ForkNode
    join_node_class=UML.JoinNode

component.provideAdapter(FlowForkNodeConnect)


class FlowDecisionNodeConnect(FlowForkDecisionNodeConnect):
    """
    Connect Flow to a DecisionNode
    """
    component.adapts(items.DecisionNodeItem, items.FlowItem)

    fork_node_class = UML.DecisionNode
    join_node_class = UML.MergeNode

component.provideAdapter(FlowDecisionNodeConnect)

# vim:sw=4:et:ai