from flask_graphql import GraphQLView
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

'''
from app.models.security import User


# Schema Objects
class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_users = SQLAlchemyConnectionField(UserObject)


schema = graphene.Schema(query=Query)

'''

'''
def init_app(flask_app):
    from .v1.graphql.schema import schema

    #schema = graphene.Schema(query=Query)

    # Routes
    flask_app.add_url_rule(
        '/graphql-api',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True # for having the GraphiQL interface
        )
    )
'''

from flask import Blueprint
from .v1.graphql.schema import schema

bp_graph = Blueprint('graphql-api', __name__)

bp_graph.add_url_rule(
    '/api/v1/graphql-api',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # for having the GraphiQL interface
    )
)