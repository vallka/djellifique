import re 
from rest_framework import serializers

import logging
logger = logging.getLogger(__name__)

# Create your views here.
class UPSSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        addressLines = instance.ShipTo_Address_AddressLine1.split(' ',2)
        if len(addressLines)>2:
            addressLines[1] = addressLines[0]+' '+addressLines[1]
            addressLines.pop(0)
        addressLines.append(instance.ShipTo_Address_AddressLine2)
        phoneCountryCode = '' 
        if instance.ShipTo_Address_CountryCode=='GB': phoneCountryCode = '44' 
        if instance.ShipTo_Address_CountryCode=='FR': phoneCountryCode = '33' 
        if instance.ShipTo_Address_CountryCode=='ES': phoneCountryCode = '34' 
        return {
            "ShipmentRequest": {
                "Shipment": {
                    "Description": instance.Description,
                    "ReferenceNumber" : {
                        "Value": instance.ReferenceNumber
                    },
                    "Shipper": {
                        "Name": "GellifiQue Ltd",
                        "AttentionName": "Margaryta",
                        "TaxIdentificationNumber": "",
                        "Phone": {
                            "Number": "447746358920"
                        },
                        "ShipperNumber": "2V813A",
                        "Address": {
                            "AddressLine": "41 Deantown Avenue Whitecraig",
                            "City": "Musselburgh",
                            "StateProvinceCode": "East Lothian",
                            "PostalCode": "EH21 8NS",
                            "CountryCode": "GB"
                        }
                    },
                    "ShipTo": {
                        "Name": instance.ShipTo_Name,
                        "AttentionName": instance.ShipTo_AttentionName,
                        "EMailAddress": instance.ShipTo_EMailAddress,
                        "Phone": {
                            "Number": re.sub(r'^0',phoneCountryCode,re.sub(r'\D','',instance.ShipTo_Phone_Number))
                        },
                        "Address": {
                            "AddressLine": addressLines,
                            "City": instance.ShipTo_Address_City,
                            "PostalCode": instance.ShipTo_Address_PostalCode,
                            "CountryCode": instance.ShipTo_Address_CountryCode
                        }
                    },
                    "ShipFrom": {
                        "Name": "GellifiQue Ltd",
                        "AttentionName": "Margaryta",
                        "TaxIdentificationNumber": "",
                        "Phone": {
                            "Number": "447746358920"
                        },
                        "ShipperNumber": "0001",
                        "Address": {
                            "AddressLine": "41 Deantown Avenue Whitecraig",
                            "City": "Musselburgh",
                            "PostalCode": "EH21 8NS",
                            "CountryCode": "GB"
                        }
                    },
                    "PaymentInformation": {
                        "ShipmentCharge": {
                            "Type": "01",
                            "BillShipper": {
                                "AccountNumber": "2V813A"
                            }
                        }
                    },
                    "Service": {
                        "Code": "11",
                        "Description": "Standard"
                    },
                    "Package": [
                        {
                            "Description": "Manicure Accessories",
                            "Packaging": {
                                "Code": "02"
                            },
                            "PackageWeight": {
                                "UnitOfMeasurement": {
                                    "Code": "KGS"
                                },
                                "Weight": str(instance.Package_Weight)
                            },
                            "PackageServiceOptions": ""
                        }
                    ],
                    "ItemizedChargesRequestedIndicator": "",
                    "RatingMethodRequestedIndicator": "",
                    "TaxInformationIndicator": "",
                    "ShipmentRatingOptions": {
                        "NegotiatedRatesIndicator": ""
                    }
                },
                "LabelSpecification": {
                    "LabelImageFormat": {
                        "Code": "GIF"
                    }
                }
            }
        }

class UPSLabelSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": {
                    "LabelImageFormat": {
                            "Code": "GIF"
                    },
                },
                "TrackingNumber": str(instance.ShippingNumber)
            }
        }        