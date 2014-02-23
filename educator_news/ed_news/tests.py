from django.test import TestCase
from django.core.urlresolvers import reverse

from ed_news.views import invalidate_cache


class EdNewsViewTests(TestCase):

    def test_index_cache(self):
        self.test_single_cache_invalidation('index')

    def test_single_cache_invalidation(self, page_name):
        """
        Very simple test for now; just testing that invalidate function works.
        Not testing triggers for invalidation.

        Request page_name, then invalidate cache.
        Cache should be invalidated, returning True.
        Then try to invalidate, and should return False.
        """
        view_path = 'ed_news:index'
        response = self.client.get(reverse('ed_news:index'))
        self.assertEqual(response.status_code, 200)

        invalidated = invalidate_cache(page_name, 'ed_news')
        self.assertEqual(invalidated, True)

        invalidated = invalidate_cache(page_name, 'ed_news')
        self.assertEqual(invalidated, False)        
