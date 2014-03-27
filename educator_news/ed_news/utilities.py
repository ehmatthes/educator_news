from ed_news.models import Submission, Article, TextPost, Comment

# Helper functions for views.py.
#  This allows views.py to simply have one function per url in urls.py.


def get_submissions(request, order_by_criteria, start_index, end_index):
    if request.user.is_authenticated() and request.user.userprofile.show_invisible:
        submissions = Submission.objects.all().order_by(*order_by_criteria).reverse()[start_index:end_index].prefetch_related('flags', 'upvotes', 'comment_set', 'submitter')
    else:
        submissions = Submission.objects.filter(visible=True).order_by(*order_by_criteria).reverse()[start_index:end_index].prefetch_related('flags', 'upvotes', 'comment_set', 'submitter')
    return submissions


