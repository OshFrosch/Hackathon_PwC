#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""

import stripe
import json
import os

from flask import Flask, render_template, jsonify, request, send_from_directory, redirect
from dotenv import load_dotenv, find_dotenv

# Setup Stripe python client library.
load_dotenv(find_dotenv())

# Ensure environment variables are set.
price = os.getenv('PRICE')

# For sample support and debugging, not required for production:
stripe.set_app_info(
    'stripe-samples/accept-a-payment/prebuilt-checkout-page',
    version='0.0.1',
    url='https://github.com/stripe-samples')

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = '2020-08-27'

application = Flask(__name__, static_url_path='/templates')


@application.route('/', methods=['GET'])
def get_example(name=None):
    return render_template('index.html', name=name)

@application.route('/canc', methods=['GET'])
def get_succ(name=None):
    return render_template('canceled.html', name=name)

@application.route('/succ', methods=['GET'])
def get_canc(name=None):
    return render_template('success.html', name=name)


# Fetch the Checkout Session to display the JSON result on the success page
@application.route('/checkout-session', methods=['GET'])
def get_checkout_session():
    id = request.args.get('sessionId')
    checkout_session = stripe.checkout.Session.retrieve(id)
    return jsonify(checkout_session)


@application.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    domain_url = os.getenv('DOMAIN')

    try:
        # Create new Checkout Session for the order
        # Other optional params include:

        # For full details see https:#stripe.com/docs/api/checkout/sessions/create
        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + '/succ?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + '/canc',
            payment_method_types=(os.getenv('PAYMENT_METHOD_TYPES') or 'card').split(','),
            mode='payment',
            # automatic_tax={'enabled': True},
            line_items=[{
                'price': os.getenv('PRICE'),
                'quantity': 1,
            }]
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 403


@application.route('/webhook', methods=['POST'])
def webhook_received():
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    print('event ' + event_type)

    if event_type == 'checkout.session.completed':
        print('🔔 Payment succeeded!')
        # Note: If you need access to the line items, for instance to
        # automate fullfillment based on the the ID of the Price, you'll
        # need to refetch the Checkout Session here, and expand the line items:
        #
        # session = stripe.checkout.Session.retrieve(
        #     data['object']['id'], expand=['line_items'])
        #
        # line_items = session.line_items
        #
        # Read more about expand here: https://stripe.com/docs/expand
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    application.debug = True
    application.run()
