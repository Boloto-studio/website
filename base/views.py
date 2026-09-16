from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import stripe

from django.conf import settings

from .forms import ContactRequestForm
from .models import BlogPost, Event, HeroSlide, MainFocus, StaffMember

# Create your views here.

stripe.api_key = settings.STRIPE_API_KEY
stripe_client = stripe.StripeClient(settings.STRIPE_API_KEY)

MONTHLY_DONATION_TARGET = 500  # Target monthly donation amount in CAD
DONATION_TIER_CACHE_TIMEOUT = 60 * 15
DONATION_TIER_CACHE_KEY = "donation_tiers"


def _build_terminal_logs():
    video_logs = []
    synced_videos = Event.objects.exclude(youtube_video_id__isnull=True).exclude(
        youtube_video_id=""
    ).order_by('-date')[:3]

    for video in synced_videos:
        playback_url = video.link or f"https://www.youtube.com/watch?v={video.youtube_video_id}"
        video_logs.append({
            "title": video.title,
            "summary": video.description,
            "timestamp": video.date,
            "kind": _("MEDIA_FILE"),
            "action_label": _("Play transmission"),
            "url": playback_url,
            "thumbnail": f"https://img.youtube.com/vi/{video.youtube_video_id}/hqdefault.jpg",
        })

    text_logs = [{
        "title": post.title,
        "summary": post.content,
        "timestamp": post.published_date,
        "kind": _("TEXT_LOG"),
        "action_label": _("Read full log"),
        "url": "",
        "thumbnail": "",
    } for post in BlogPost.objects.all().order_by('-published_date')[:6]]

    combined_logs = sorted(
        [*video_logs, *text_logs],
        key=lambda item: item["timestamp"],
        reverse=True,
    )
    return combined_logs[:6]

def _donation_tiers():
    cached_tiers = cache.get(DONATION_TIER_CACHE_KEY)
    if cached_tiers is not None:
        return cached_tiers

    try:
        products = stripe.Product.search(
            query="active:'true' AND metadata['sub_type']:'donation'",
        ).to_dict()
    except stripe.error.StripeError:
        cache.set(DONATION_TIER_CACHE_KEY, [], timeout=DONATION_TIER_CACHE_TIMEOUT)
        return []

    tiers = []
    for product in products.get("data", []):
        metadata = product.get("metadata") or {}
        price_id = product.get("default_price")
        price = None
        recurring_interval = _("month")

        if price_id:
            try:
                price_data = stripe.Price.retrieve(price_id).to_dict()
                if price_data.get("unit_amount") is not None:
                    price = str(int(price_data["unit_amount"]) // 100)
                if price_data.get("recurring") and price_data["recurring"].get("interval"):
                    recurring_interval = price_data["recurring"]["interval"]
            except stripe.error.StripeError:
                price = metadata.get("price")

        if price is None:
            price = metadata.get("price", "0")

        slug = (metadata.get("slug") or product.get("name").split()[0] or "donation-tier").lower().replace(" ", "-")
        name = metadata.get("display_name") or product.get("name").split()[0] or slug.replace("-", " ").title()
        features = [feature["name"] for feature in product.get("marketing_features", [])]
        if not features:
            features = [_("Discord role"), _("Early updates")]

        tier = {
            "slug": slug,
            "name": _(name),
            "price": price,
            "interval": _(recurring_interval),
            "features": [_(feature) for feature in features],
            "link": reverse("donation_redirect", args=[slug]),
            "featured": metadata.get("featured_label", "") != "",
            "featured_label": metadata.get("featured_label") or "",
            "stripe_id": metadata.get("stripe_price_id") or price_id or "",
            "stripe_test_id": metadata.get("stripe_test_price_id") or metadata.get("stripe_price_id") or price_id or "",
        }

        tiers.append(tier)
    tiers.sort(key=lambda x: int(x["price"]))
    cache.set(DONATION_TIER_CACHE_KEY, tiers, timeout=DONATION_TIER_CACHE_TIMEOUT)
    return tiers


def home(request):
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order', '-created_at')
    return render(request, "base/home.html", {
        "hero_slides": hero_slides,
        "terminal_logs": _build_terminal_logs(),
    })


def studio(request):
    return render(request, "base/studio.html", {
        "staff": StaffMember.objects.all(),
        "main_focus": MainFocus.objects.first(),
    })

@login_required
def donation_redirect(request, tier_slug):
    if settings.DEBUG:
        if tier_slug == "scavenger":
            return redirect(f"https://buy.stripe.com/test_14A4gz7Fybg9f1ndtG57W01?client_reference_id={request.user.id}")
        elif tier_slug == "operative":
            return redirect(f"https://buy.stripe.com/test_aFa9ATe3W2JDcTf89m57W02?client_reference_id={request.user.id}")
        elif tier_slug == "overseer":
            return redirect(f"https://buy.stripe.com/test_4gM28raRK6ZT6uR9dq57W00?client_reference_id={request.user.id}")
    else:
        if tier_slug == "scavenger":
            return redirect(f"https://donate.stripe.com/14A4gz7Fybg9f1ndtG57W01?client_reference_id={request.user.id}")
        elif tier_slug == "operative":
            return redirect(f"https://donate.stripe.com/28EeVd0d6doh8CZdtG57W03?client_reference_id={request.user.id}")
        elif tier_slug == "overseer":
            return redirect(f"https://donate.stripe.com/8x25kDbVObg92eB89m57W04?client_reference_id={request.user.id}")

def donation(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    start_timestamp = int(thirty_days_ago.timestamp())
    total_monthly_donations = 0
    donations_count = 0
    try:
        payments = stripe.PaymentIntent.list(
            created={"gte": start_timestamp},
            limit=100
        )

        for payment in payments.auto_paging_iter():
            # Process your payments
            print(payment.id, payment.amount)
            if payment.amount is not None:
                total_monthly_donations += payment.amount
    except stripe.error.StripeError:
        total_monthly_donations = 0
        donations_count = 0

    total_monthly_donations = total_monthly_donations / 100

    print(f"Total monthly donations: {total_monthly_donations}, Donations count: {donations_count}")

    return render(request, "base/donation.html", {
        "donation_progress": {
            "percent": min(100, int((total_monthly_donations / MONTHLY_DONATION_TARGET) * 100)),
            "display": "████████░░",
            "target": MONTHLY_DONATION_TARGET,
            "total": total_monthly_donations,
            "count": donations_count,
        },
        "donation_tiers": _donation_tiers(),
        "total_monthly_donations": total_monthly_donations,
        "donations_count": donations_count,
    })

def fulfill_checkout(session_id):
    # Retrieve the Checkout Session from the API with line_items expanded
    checkout_session = stripe_client.v1.checkout.sessions.retrieve(
        session_id,
        params={'expand': ['line_items']},
    )
    account_id = checkout_session["client_reference_id"]

    # Check the Checkout Session's payment_status property
    # to determine if fulfillment should be performed
    if checkout_session.payment_status != 'unpaid':
        user = User.objects.get(id=account_id)
        frog = user.frog
        tier = checkout_session["line_items"]["data"][0]["description"].lower().replace("tier", "").strip()
        frog.stripe_customer_id = checkout_session["customer"]
        frog.tier = tier
        frog.save()
        return stripe.Subscription.list(customer=frog.stripe_customer_id)['data'][0], tier

@login_required
def modify_subscription(request):
    if request.method == "POST":
        new_tier_str = request.POST.get("tier")
        new_tier = next((tier for tier in _donation_tiers() if tier['slug'] == new_tier_str), None)
        frog = request.user.frog

        # Retrieve the customer's subscriptions
        subscriptions = stripe.Subscription.list(customer=frog.stripe_customer_id)

        if subscriptions.data:
            subscription = subscriptions.data[0]  # Assuming the user has only one subscription

            # Update the subscription with the new tier
            stripe.Subscription.modify(
                subscription.id,
                items=[
                {"deleted": True, "id": subscription['items']['data'][0]['id']},
                {"price": new_tier['stripe_id'] if not settings.DEBUG else new_tier['stripe_test_id'], "quantity": 1}
            ])
            frog.tier = new_tier.lower().replace("tier", "").strip()
            frog.save()
            messages.success(request, _("Your subscription has been updated."))
        else:
            messages.error(request, _("You do not have an active subscription to modify."))

    return redirect("donation")

@login_required
def cancel_subscription(request):
    frog = request.user.frog
    subscriptions = stripe.Subscription.list(customer=frog.stripe_customer_id)

    if subscriptions.data:
        subscription = subscriptions.data[0]  # Assuming the user has only one subscription
        stripe.Subscription.delete(subscription.id)
        frog.tier = 'frog'
        frog.save()
        messages.success(request, _("Your subscription has been canceled."))
    else:
        messages.error(request, _("You do not have an active subscription to cancel."))

    return redirect("donation")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe_client.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if (
        event['type'] == 'checkout.session.completed'
        or event['type'] == 'checkout.session.async_payment_succeeded'
    ):
        fulfill_checkout(event['data']['object']['id'])

    return HttpResponse(status=200)

def donation_confirmed(request, session_id):
    # Retrieve the Checkout Session from the API
    checkout_session = stripe_client.v1.checkout.sessions.retrieve(session_id)
    _, tier = fulfill_checkout(session_id)
    amount_paid = checkout_session["amount_total"] / 100  # Convert from cents to dollars
    percentage_contributed = min(100, int(amount_paid / MONTHLY_DONATION_TARGET * 100))
    return render(request, "base/donation_confirmed.html", {
        "checkout_session": checkout_session,
        "tier": tier,
        "percentage_contributed": percentage_contributed
    })

def under_construction(request):
    return render(request, "base/under_construction.html")

def contact(request):
    if request.method == "POST":
        form = ContactRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Transmission received. We will respond when the line is clear."))
            return render(request, "base/contact.html", {
                "nav_key": "contact",
                "form": ContactRequestForm(),
                "transmission_complete": True,
            })
    else:
        form = ContactRequestForm()

    return render(request, "base/contact.html", {
        "nav_key": "contact",
        "form": form,
    })