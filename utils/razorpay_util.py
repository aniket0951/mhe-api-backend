from typing import Any
import razorpay
from django.conf import settings

KEY_ID = settings.RAZOR_KEY_ID
KEY_SECRET = settings.RAZOR_KEY_SECRET
APP_TITLE = settings.RAZOR_APP_TITLE
APP_VERSION = settings.RAZOR_APP_VERSION
PAYMENT_CURRENCY = settings.RAZOR_PAYMENT_CURRENCY
AMOUNT_OFFSET = settings.RAZOR_AMOUNT_OFFSET

class RazorPayUtil:

    def __init__(self,
        key_id=KEY_ID,
        key_secret=KEY_SECRET,
        app_title=APP_TITLE,
        app_version=APP_VERSION,
        invoice_id=None,
        customer_id=None,
        payment_id=None,
        order_id=None,
        refund_id=None
    ):
        self.client = razorpay.Client(auth=(key_id,key_secret))
        self.client.set_app_details({"title":app_title,"version":app_version})

        self.invoice_status = None
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.payment_id = payment_id
        self.order_id = order_id
        self.refund_id = refund_id
        
    def set_order_id(self,order_id):
        self.order_id = order_id

    def set_invoice_id(self,invoice_id):
        self.invoice_id = invoice_id
    
    def set_payment_id(self,payment_id):
        self.payment_id = payment_id
    
    def set_refund_id(self,refund_id):
        self.refund_id = refund_id
    
    def set_customer_id(self,customer_id):
        self.customer_id = customer_id
    
    def set_order_status(self,order_status):
        self.order_status = order_status
        
    def create_order(
        self,
        amount:float,
        description:str="",
        currency:str=PAYMENT_CURRENCY
    ):
        if AMOUNT_OFFSET:
            amount *= int(AMOUNT_OFFSET)
        create_order_data = {
            "amount":amount,
            "currency": currency,
            "notes":{
                "description":description
            }
        }
        order_data = self.client.order.create(data=create_order_data)

        self.set_order_id(order_data.get("id"))
        self.set_order_status(order_data.get("status"))

        return order_data

    def fetch_order(self):
        if not self.order_id:
            return None
        return self.client.order.fetch(self.order_id)
    
    def fetch_payments_of_order(self):
        return self.client.order.payments(self.order_id)

    def fetch_invoice(self):
        if not self.invoice_id:
            return None
        invoice_data =  self.client.invoice.fetch(self.invoice_id)
        self.set_payment_id(invoice_data.get("payment_id"))
        self.set_invoice_status(invoice_data.get("status"))
        return invoice_data

    def fetch_payment(self):
        return self.client.payment.fetch(self.payment_id)

    def capture_payment(self,amount):
        if not amount or not self.payment_id:
            return None
        if AMOUNT_OFFSET:
            amount *= int(AMOUNT_OFFSET)
        return self.client.payment.capture(self.payment_id,amount)

    def initiate_refunt(self,amount_to_be_refunded):
        if not amount_to_be_refunded or not self.payment_id:
            return None
        if AMOUNT_OFFSET:
            amount_to_be_refunded *= int(AMOUNT_OFFSET)
        refund_data = self.client.payment.refund(self.payment_id,int(amount_to_be_refunded))
        self.refund_id = refund_data.get("id")
        return refund_data

    def fetch_refund(self):
        if not self.refund_id:
            return None
        return self.client.refund.fetch(self.refund_id)