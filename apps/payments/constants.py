class PaymentConstants:

    JSON_CONTENT_TYPE = 'application/json'

    URL_ITEM_TERIFF_PRICE = '/api/master_data/items_tariff_price'
    URL_CONSULTATION_CHARGES =  '/api/master_data/consultation_charges'
    URL_HEALTH_PACKAGE_PRICE = '/api/health_packages/health_package_price'
    URL_OP_BILL_DETAILS = '/api/payments/op_bill_details'

    APPOINTMENT_PACKAGE_CODE = "NA"
    APPOINTMENT_TRANSACTION_TYPE = "APP"
    APPOINTMENT_MODE_HV = "HV"
    APPOINTMENT_MODE_VC = "VC"
    APPOINTMENT_MODE_PR = "PR"

    HEALTH_PACKAGE_TRANSACTION_TYPE = "HC"    
    UHID_TRANSACTION_TYPE = "REG"
    OP_BILL_TRANSACTION_TYPE = "OPB"
    IP_DEPOSIT_TRANSACTION_TYPE = "IPD"
    
    UHID_PAYMENT_FRC_ID = "TMP.1062686"
    TERRIF_PRICE_ITEM_CODE = 'AREG001'

    MANIPAL_OPD_CONS_CHARGES= "OPDConsCharges"
    MANIPAL_VC_CONS_CHARGES = "VCConsCharges"
    MANIPAL_PR_CONS_CHARGES = "PRConsCharges"

    ERROR_MESSAGE_PRICE_UPDATED = "Price is Updated"

    RAZORPAY_PAYMENT_CURRENCY = "INR"

    RAZORPAY_APPOINTMENT_PAYMENT_DESCRIPTION = "Payment transaction for booking appointment"
    RAZORPAY_HEALTH_PACKAGE_PURCHASE_DESCRIPTION = "Payment transaction for health package purchase"
    RAZORPAY_UHID_PURCHASE_DESCRIPTION = "Payment transaction for UHID purchase"
    RAZORPAY_OP_BILL_PAYMENT_DESCRIPTION = "Payment transaction for OP BILL"
    RAZORPAY_IP_DEPOSIT_PAYMENT_DESCRIPTION = "Payment transaction for OP BILL"

    RAZORPAY_PAYMENT_STATUS_CREATED = "created"
    RAZORPAY_PAYMENT_STATUS_PAID = "paid"
    RAZORPAY_PAYMENT_STATUS_CAPTURED = "captured"