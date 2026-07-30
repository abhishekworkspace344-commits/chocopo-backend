import codecs

routes_code = """
@api.route("/admin/products", methods=["POST"])
@jwt_required()
def admin_create_product():
    data = request.get_json() or {}
    
    category_id = data.get("category_id")
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip() or None
    price = data.get("price")
    discount_price = data.get("discount_price")
    offers = str(data.get("offers", "")).strip() or None
    image_url = str(data.get("image_url", "")).strip() or None
    preparation_minutes = data.get("preparation_minutes", 15)
    is_available = data.get("is_available", True)
    is_featured = data.get("is_featured", False)

    if not name or not price or not category_id:
        return jsonify({"message": "Name, price, and category are required."}), 400

    product = Product(
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        discount_price=discount_price,
        offers=offers,
        image_url=image_url,
        preparation_minutes=preparation_minutes,
        is_available=is_available,
        is_featured=is_featured
    )
    db.session.add(product)
    db.session.commit()
    
    return jsonify({"message": "Product created successfully", "product_id": product.id}), 201

@api.route("/admin/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def admin_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    
    if "category_id" in data:
        product.category_id = data["category_id"]
    if "name" in data:
        product.name = str(data["name"]).strip()
    if "description" in data:
        product.description = str(data["description"]).strip() or None
    if "price" in data:
        product.price = data["price"]
    if "discount_price" in data:
        product.discount_price = data.get("discount_price") # Can be null
    if "offers" in data:
        product.offers = str(data.get("offers", "")).strip() or None
    if "image_url" in data:
        product.image_url = str(data.get("image_url", "")).strip() or None
    if "preparation_minutes" in data:
        product.preparation_minutes = data["preparation_minutes"]
    if "is_available" in data:
        product.is_available = data["is_available"]
    if "is_featured" in data:
        product.is_featured = data["is_featured"]

    db.session.commit()
    return jsonify({"message": "Product updated successfully"})

@api.route("/admin/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"})
"""

with codecs.open('routes.py', 'a', encoding='utf-8') as f:
    f.write(routes_code)
