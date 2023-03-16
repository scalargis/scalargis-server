from math import ceil

class Pagination(object):

    def __init__(self, page, per_page, total_count, left_edge=None, left_current=None, right_edge=None, right_current=None):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
        self.left_edge = left_edge
        self.left_current = left_current
        self.right_edge = right_edge
        self.right_current = right_current

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_edge=2, right_current=5):
        last = 0
        _left_edge = left_edge
        _left_current = left_current
        _right_edge = right_edge
        _right_current = right_current
        if self.left_edge:
            _left_edge = self.left_edge
        if self.left_current:
            _left_current = self.left_current
        if self.right_edge:
            _right_edge = self.right_edge
        if self.right_current:
            _right_current = self.right_current
        for num in range(1, self.pages + 1):
            if num <= _left_edge or \
               (num > self.page - _left_current - 1 and \
                num < self.page + _right_current) or \
                num > self.pages - _right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
