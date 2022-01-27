from flask_restx import reqparse

pagination_arguments = reqparse.RequestParser()
pagination_arguments.add_argument('page', type=int, required=False, default=1, help='Página')
pagination_arguments.add_argument('filter', type=str, required=False, help='Filtro')
pagination_arguments.add_argument('per_page', type=int, required=False, choices=[5, 10, 20, 25, 30, 40, 50, 1000],
                                  default=10, help='Results per page {error_msg}')

parser_records_with_page = reqparse.RequestParser()
parser_records_with_page.add_argument('page', type=int, required=False, default=1, help='Página')
parser_records_with_page.add_argument('filter', type=str, required=False, help='Filtro')
parser_records_with_page.add_argument('sort', type=str, required=False, help='Ordenação')
parser_records_with_page.add_argument('per_page', type=int, required=False, choices=[5, 10, 20, 25, 30, 40, 50, 100,
                                  200, 500, 1000], default=10, help='Results per page {error_msg}')

parser_list = reqparse.RequestParser()
parser_list.add_argument('filter', type=str, required=False, help='Filtro')
parser_list.add_argument('sort', type=str, required=False, help='Ordenação')

parser_delete_records = reqparse.RequestParser()
parser_delete_records.add_argument('filter', type=str, required=False, help='Filtro')
