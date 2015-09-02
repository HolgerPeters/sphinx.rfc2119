from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.compat import make_admonition
from sphinx.locale import _

def setup(app):
    app.add_config_value('rfc2119_include', True, True)
    app.add_node(mandatorylist)
    app.add_node(recommendationlist)
    app.add_node(optionallist)

    for node_type in (mandatory, recommended, optional):
        app.add_node(
            node_type,
            html=(visit_rfc2119_node, depart_rfc2119_node),
            latex=(visit_rfc2119_node, depart_rfc2119_node),
            text=(visit_rfc2119_node, depart_rfc2119_node))

    app.add_directive('must', MustDirective)
    app.add_directive('must_not', MustNotDirective)
    app.add_directive('shall', ShallDirective)
    app.add_directive('shall_not', ShallNotDirective)
    app.add_directive('required', RequiredDirective)
    app.add_directive('should', ShouldDirective)
    app.add_directive('should_not', ShouldNotDirective)
    app.add_directive('recommended', RecommendedDirective)
    app.add_directive('not_recommended', NotRecommendedDirective)
    app.add_directive('optional', OptionalDirective)
    app.add_directive('may', MayDirective)

    app.add_directive('mandatorylist', MandatoryListDirective)
    app.add_directive('recommendationlist', RecommendationListDirective)
    app.add_directive('optionallist', OptionalListDirective)

    app.connect('doctree-resolved', process_rfc2119_nodes)
    app.connect('env-purge-doc', purge_rfc2119_mandatory)
    app.connect('env-purge-doc', purge_rfc2119_recommendation)
    app.connect('env-purge-doc', purge_rfc2119_optional)

    return {"version": "0.2"}


class mandatory(nodes.Admonition, nodes.Element): pass
class recommended(nodes.Admonition, nodes.Element): pass
class optional(nodes.Admonition, nodes.Element): pass
class mandatorylist(nodes.General, nodes.Element): pass
class recommendationlist(nodes.General, nodes.Element): pass
class optionallist(nodes.General, nodes.Element): pass


def visit_rfc2119_node(self, node):
    self.visit_admonition(node)

def depart_rfc2119_node(self, node):
    self.depart_admonition(node)


class MandatoryListDirective(Directive):
    has_content = True
    def run(self):
        return [mandatorylist('')]

class RecommendationListDirective(Directive):
    has_content = True
    def run(self):
        return [recommendationlist('')]

class OptionalListDirective(Directive):
    has_content = True
    def run(self):
        return [optionallist('')]


class rfc2119Directive(Directive):
    """ An abstract base for rfc2199 requirements."""
    # labels not used because this class is treated as abstract
    # we expcet subclasses to overwrite them
    label = "rfc2119"
    requirement_class = "rfc2119"
    has_content = True
    def run(self):
        env = self.state.document.settings.env
        #env.app.warn('DEBUG')
        targetid = "%s-%d" % (
            self.requirement_class,
            env.new_serialno(self.requirement_class))
        targetnode = nodes.target('', '', ids=[targetid])

        ad = make_admonition(
            mandatory, self.name, [_(self.label)], self.options,
            self.content, self.lineno, self.content_offset,
            self.block_text, self.state, self.state_machine)

        env_data_name = "rfc2119_all_%s" % self.requirement_class
        if not hasattr(env, env_data_name):
            exec("env.%s = []" % env_data_name)

        env_data = eval("env.%s" % env_data_name)
        env_data.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'rfc2119': ad[0].deepcopy(),
            'target': targetnode})

        return [targetnode] + ad


class OptionalDirective(rfc2119Directive):
    label = "Optional"
    requirement_class = "optional"

class MayDirective(rfc2119Directive):
    label = "May"
    requirement_class = "optional"

class ShouldDirective(rfc2119Directive):
    label = "Should"
    requirement_class = "recommendation"

class ShouldNotDirective(rfc2119Directive):
    label = "Should Not"
    requirement_class = "recommendation"

class RecommendedDirective(rfc2119Directive):
    label = "Recommended"
    requirement_class = "recommendation"

class NotRecommendedDirective(rfc2119Directive):
    label = "Not Recommended"
    requirement_class = "recommendation"

class MustDirective(rfc2119Directive):
    label = "Must"
    requirement_class = "mandatory"

class MustNotDirective(rfc2119Directive):
    label = "Must Not"
    requirement_class = "mandatory"

class ShallDirective(rfc2119Directive):
    label = "Shall"
    requirement_class = "mandatory"

class ShallNotDirective(rfc2119Directive):
    label = "Shall Not"
    requirement_class = "mandatory"

class RequiredDirective(rfc2119Directive):
    label = "Required"
    requirement_class = "mandatory"


def purge_rfc2119_mandatory(app, env, docname):
    if not hasattr(env, 'rfc2119_all_mandatorys'):
        return
    env.rfc2119_all_mandatory = [mandatory for mandatory in env.rfc2119_all_mandatory if mandatory['docname'] != docname]

def purge_rfc2119_recommendation(app, env, docname):
    if not hasattr(env, 'rfc2119_all_recommendation'):
        return
    env.rfc2119_all_recommendation = [rec for rec in env.rfc2119_all_recommendation if rec['docname'] != docname]

def purge_rfc2119_optional(app, env, docname):
    if not hasattr(env, 'rfc2119_all_optional'):
        return
    env.rfc2119_all_optional = [rec for rec in env.rfc2119_all_optional if rec['docname'] != docname]


# TODO - for the other node types, not just mandatory
def process_rfc2119_nodes(app, doctree, fromdocname):
    base_types =  (mandatory, recommended, optional)
    list_types = (mandatorylist, recommendationlist, optionallist)

    if not app.config.rfc2119_include:
        for node_type in base_types:
            for node in doctree.traverse(node_type):
                node.parent.remove(node)

    env = app.builder.env

    for node_type in list_types:
        for node in doctree.traverse(node_type):
            if not app.config.rfc2119_include:
                node.replace_self([])
                continue

            content = []

            if node_type == mandatory:
                env_data = env.rfc2119_all_mandatory
            elif node_type == recommendationlist:
                env_data = env.rfc2119_all_recommendation
            else:
                env_data = env.rfc2119_all_optional

            for info in env_data:
                para = nodes.paragraph()
                filename = env.doc2path(info['docname'], base=None)
                description = (
                    _('(The original entry is located in %s, line %d and can be found ') %
                    (filename, info['lineno']))
                para += nodes.Text(description, description)

                newnode = nodes.reference('', '')
                innernode = nodes.emphasis(_('here'), _('here'))
                newnode['refdocname'] = info['docname']
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, info['docname'])
                newnode['refuri'] += '#' + info['target']['refid']
                newnode.append(innernode)
                para += newnode
                para+= nodes.Text('.)', '.)')

                content.append(info['rfc2119'])
                content.append(para)

            node.replace_self(content)
