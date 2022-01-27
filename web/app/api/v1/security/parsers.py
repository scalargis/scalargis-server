from flask_restx import reqparse

parser = reqparse.RequestParser()
parser.add_argument('username', type=str, required=True,
                           help='Username or email',
                           location='json')
parser.add_argument('password', type=str, required=True,
                           help='Password',
                           location='json')