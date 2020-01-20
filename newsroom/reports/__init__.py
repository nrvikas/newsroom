from flask import Blueprint
from .reports import get_company_saved_searches, get_subscriber_activity_report, \
    get_user_saved_searches, get_company_products, get_product_stories, get_company_report, \
    get_content_activity_report, get_company_api_usage

blueprint = Blueprint('reports', __name__)


reports = {
    'company-saved-searches': get_company_saved_searches,
    'user-saved-searches': get_user_saved_searches,
    'company-products': get_company_products,
    'product-stories': get_product_stories,
    'company': get_company_report,
    'subscriber-activity': get_subscriber_activity_report,
    'content-activity': get_content_activity_report,
    'company-news-api-usage': get_company_api_usage,
}


from . import views  # noqa
