from datetime import datetime, timedelta, timezone
import hashlib
import json
import sys

import requests

NOW = datetime.now(timezone.utc)

session = requests

if not "request" in globals():
    request = {
        "api": "caps"
    }

if "verbose" in request and request["verbose"]:
    verbose = True
else:
    verbose = False
    
material_package_to_name_mapping = {
    "/pub/std/manufacturing/material/plastic:pla": "PLA",
    "/pub/std/manufacturing/material/plastic:abs": "ABS",
    "/pub/std/manufacturing/material/plastic:nylon": "Nylon"
}

headers_cart_checkout = {
    "apicode": request['parameters']['apiKey']
}


headers_create_cart = {
    "apicode": request['parameters']['apiKey'],
    "content-type": "application/json"
}

headers_create_cart_items = {}
    
headers_get_pricing = {
    "apicode": request['parameters']['apiKey'],
    "content-type": "application/json"
}

headers_upload_model = {}

headers_get_materials = {
    "content-type": "application/json"
}

def api_call(endpoint, data=None, files=None, json=None, headers={}, method="POST"):
    global request
    global session
    global verbose

    url = request["parameters"]["url"] + endpoint
    
    if method.upper() == "GET":
        response = session.get(
            url,
            headers=headers,
            params=data,
        )
    elif method.upper() == "POST":
        response = session.post(
            url,
            headers=headers,
            data=data,
            json=json,
            files=files,
        )
    else:
        raise Exception("Unsupported HTTP method. Use 'GET' or 'POST'.")
    
    try:
        json_response = response.json()
    except Exception as e:
        raise Exception(f"Failed to load Response: {e}")
    
    if "error" in json_response:
        raise Exception(f"Request Error: {json_response}")
    return json_response
    

def cart_checkout(cart_id):
    global headers_cart_checkout
    
    form_data = {
        "cartID":cart_id,
        "myOrderReference":"",
        "directMailingAllowed":"false",
        "shipmentService":"Express",
        "remarks":"",
        "languageCode":"en"
    }
    files = {
        "data": ("blob", json.dumps(form_data), "application/json")
    }
    response = api_call(
        "/web-api/order/post",
        files=files,
        headers=headers_create_cart
    )
    return response
    

def get_cart_items_id_list(cart_items):
    return [
        { 
            "CartItemID": cart_item["cartItemID"]
        } for cart_item in cart_items
    ]

def create_cart(cart_items):
    global request
    global headers_create_cart
    
    shipping_address = {
        "FirstName": request["user"]["shippingAddress"]["firstName"],
        "LastName": request["user"]["shippingAddress"]["lastName"],
        "Email": request["user"]["shippingAddress"]["email"],
        "Phone": request["user"]["shippingAddress"]["phone"],
        "Company": request["user"]["shippingAddress"]["company"],
        "Line1": request["user"]["shippingAddress"]["line1"],
        "Line2": request["user"]["shippingAddress"].get("line2"),
        "CountryCode": request["user"]["shippingAddress"]["countryCode"],
        "StateCode": request["user"]["shippingAddress"]["stateCode"],
        "ZipCode": request["user"]["shippingAddress"]["zipCode"],
        "City": request["user"]["shippingAddress"]["city"]
    }
    billing_address = {
        "FirstName": request["user"]["billingAddress"]["firstName"],
        "LastName": request["user"]["billingAddress"]["lastName"],
        "Email": request["user"]["billingAddress"]["email"],
        "Phone": request["user"]["billingAddress"]["phone"],
        "Company": request["user"]["billingAddress"]["company"],
        "Line1": request["user"]["billingAddress"]["line1"],
        "Line2": request["user"]["billingAddress"].get("line2"),
        "CountryCode": request["user"]["billingAddress"]["countryCode"],
        "StateCode": request["user"]["billingAddress"]["stateCode"],
        "ZipCode": request["user"]["billingAddress"]["zipCode"],
        "City": request["user"]["billingAddress"]["city"]
    }

    
    form_data = {
        "MyCartReference": "My cart",
        "Currency": "USD",
        "LanguageCode": "en",
        "ReturnUrl": "http://mysite.com/success.html",
        "OrderConfirmationUrl": "http://mysite.com/confirm.html",
        "FailureUrl": "http://mysite.com/failure.html",
        "PromoCode":"", 
        "CartItems":cart_items,
        "ShippingInfo": shipping_address,
        "BillingInfo": billing_address
    }
    response = api_call(
        "/web-api/cart/post",
        json=form_data,
        headers=headers_create_cart
    )
    return response

def create_cart_item_obj(
    part_id,
    model_id,
    material_id,
    finish_id,
    file_units, 
    x_dim_mm, 
    y_dim_mm, 
    z_dim_mm,
    volume_cm3,
    surface_cm2,
    quantity=1
):
    return {
        "toolID": request['parameters']['toolID'],
        "modelID": model_id,
        "MyCartItemReference": hashlib.md5(part_id.encode("utf-8")).hexdigest(),
        "fileUnits": file_units,
        "fileScaleFactor": "1",
        "materialID": material_id,
        "finishID": finish_id,
        "quantity": quantity,
        "xDimMm": x_dim_mm,
        "yDimMm": y_dim_mm,
        "zDimMm": z_dim_mm,
        "volumeCm3": volume_cm3,
        "surfaceCm2": surface_cm2,
        "iMatAPIPrice": "0",
        "mySalesPrice": "0",
    }

def create_cart_items(
    cart_items
):
    global request
    global headers_create_cart_items
    
    form_data = {
        "cartItems":cart_items,
        "currency": "USD"
    }
    
    files = {
        "data": ("blob", json.dumps(form_data), "application/json")
    }
    response = api_call(
        "/web-api/cartitems/register",
        files=files,
        headers=headers_create_cart_items
    )
    return response

def get_pricing_by_model_id(model_id, material_id, finish_id, quantity=1):
    global headers_get_pricing
    
    form_data = {
        "models": [
            {
                "modelID": model_id,
                "materialID": material_id,
                "finishID": finish_id,
                "quantity": quantity,
                "scale": "1.0"
            }
        ],
        "currency": "USD"
    }
    response = api_call(
        "/web-api/pricing/model",
        json=form_data,
        headers=headers_get_pricing
    )
    return response


def api_upload_file(part_id, model):
    global headers_upload_model
    global request
    
    name = hashlib.md5(part_id.encode("utf-8")).hexdigest() + ".step"
    # Define the form data
    form_data = {
        "fileUnits": "mm",
        "fileUrl": ""
    }

    # Prepare the file for uploading
    files = {
        "file": (name, model, "application/octet-stream")
    }
    response = api_call(
        f"/web-api/tool/{request['parameters']['toolID']}/model",
        files=files,
        data=form_data,
        headers=headers_upload_model
    )

    return response

def set_material(material):
    global material_package_to_name_mapping
    
    api_materials = api_get_materials()
    api_material = material_package_to_name_mapping[material]
    
    if api_material in api_materials:
        return api_materials[api_material]["id"]
    
    raise Exception("Unknown material: {}".format(api_material))

def set_finish(material, finish):
    global material_package_to_name_mapping
    
    api_materials = api_get_materials()
    api_material = material_package_to_name_mapping[material]
    api_material_entry = api_materials[api_material]
    
    for api_finish_entry in api_material_entry["finishes"]:
        if api_finish_entry["name"] == finish:
            return api_finish_entry["id"]
    raise Exception("Unknown finish: {}".format(finish))
    

def api_get_materials():
    global headers_get_materials
    
    response = api_call(
        "/web-api/materials?user=support@partcad.org",
        method="GET",
        headers=headers_get_materials
    )
    materials = {}
    for material in response["materials"]:
        materials[material["name"]] = {
            "id": material["materialID"],
            "finishes": [
                {
                    "id": finish["finishID"],
                    "name": finish["name"]
                } for finish in material["finishes"]
            ]
        }
    return materials

def create_cart_internal(request):
    parts = request["cart"]["parts"]
    
    # price = 0.0
    cart_items = []
    for part_name, part in parts.items():
        material = set_material(part['material'])
        finish = set_finish(part['material'], part['finish'])
        response = api_upload_file(part_name, part["binary"])
        cart_items.append(create_cart_item_obj(
            part_id=part_name,
            model_id=response["modelID"],
            material_id=material,
            finish_id=finish,
            file_units=response["fileUnits"],
            x_dim_mm=response["xDimMm"],
            y_dim_mm=response["yDimMm"],
            z_dim_mm=response["zDimMm"],
            volume_cm3=response["volumeCm3"],
            surface_cm2=response["surfaceCm2"],
            quantity=part["count"]
        ))
        # price += float(get_pricing_by_model_id(response["modelID"], material, finish, quantity=part["count"]))
    cart_items = create_cart_items(
        cart_items=cart_items
    )
 
    return create_cart(get_cart_items_id_list(cart_items["cartItems"]))


if __name__ == "caps":
    materials = api_get_materials()
    output = {
        "name": "imaterialise",
        "formats": ["step"],
        "materials": {}
    }
    supported_materials = {
        "PLA": "/pub/std/manufacturing/material/plastic:pla",
        "ABS": "/pub/std/manufacturing/material/plastic:abs",
        "Nylon": "/pub/std/manufacturing/material/plastic:nylon"
    }
    for supported_material in supported_materials:
        if supported_material in materials:
            output["materials"][supported_materials[supported_material]] = {
                "finishes": materials[supported_material]["finishes"],
                "colors": materials[supported_material]["finishes"]
            }
    sys.stderr.write("Materials: {}\n".format(output["materials"]))

elif __name__ == "avail":
    vendor = request.get("vendor", None)
    sku = request.get("sku", None)

    if vendor == "imaterialise":
        output = {
            "available": True,
        }
    else:
        output = {
            "available": False,
        }

elif __name__ == "quote":
    cart = create_cart_internal(request)
    
    output = {
        "qos": request["cart"]["qos"],
        "price": cart.get("subTotalPrice", 0),
        "expire": (NOW + timedelta(hours=1)).timestamp(),
        "cartId": cart.get("cartID", None),
        "etaMin": (NOW + timedelta(hours=1)).timestamp(),
        "etaMax": (NOW + timedelta(hours=2)).timestamp(),
    }

elif __name__ == "order":
    cart = create_cart_internal(request)
    cart_id = cart.get("cartID", None)
    sys.stderr.write(f"CART ID: {cart['cartID']}\n")
    
    order = cart_checkout(cart_id=cart_id)
    # sys.stderr.write(f"ORDER: {order}\n")
    output = {
        "qos": request["cart"]["qos"],
        "price": cart.get("subTotalPrice", 0),
        "expire": (NOW + timedelta(hours=1)).timestamp(),
        "orderId": order.get("orderID", None),
        "etaMin": (NOW + timedelta(hours=1)).timestamp(),
        "etaMax": (NOW + timedelta(hours=2)).timestamp(),
    }

else:
    raise Exception("Unknown API: {}".format(__name__))
