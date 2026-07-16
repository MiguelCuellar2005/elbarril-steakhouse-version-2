from app import app, db, Categoria, Plato

def get_or_create_categoria(tipo, nombre_es, nombre_fr, orden):
    categoria = Categoria.query.filter_by(tipo=tipo, nombre_es=nombre_es).first()
    if categoria:
        return categoria
    categoria = Categoria(tipo=tipo, nombre_es=nombre_es, nombre_fr=nombre_fr, orden=orden)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def get_or_create_plato(categoria_id, nombre_es, nombre_fr, precio):
    plato = Plato.query.filter_by(categoria_id=categoria_id, nombre_es=nombre_es).first()
    if plato:
        plato.nombre_fr = nombre_fr
        plato.precio = precio
        db.session.commit()
        return plato
    plato = Plato(
        categoria_id=categoria_id,
        nombre_es=nombre_es,
        nombre_fr=nombre_fr,
        precio=precio,
        disponible=True
    )
    db.session.add(plato)
    db.session.commit()
    return plato


with app.app_context():
    # ---------- CATEGORÍAS FOOD TRUCK ----------
    cat_platos_ft = get_or_create_categoria("foodtruck", "Platos", "Plats", 1)
    cat_extras_ft = get_or_create_categoria("foodtruck", "Extras", "Extras", 2)
    cat_entradas_ft = get_or_create_categoria("foodtruck", "Entradas", "Entrées", 3)
    cat_postres_ft = get_or_create_categoria("foodtruck", "Postres", "Desserts", 4)

    print("Categorías del Food Truck listas.")

    get_or_create_plato(cat_platos_ft.id, "Papas con cerdo desmechado", "Frites au porc effiloché", 16.50)
    get_or_create_plato(cat_platos_ft.id, "Nachos con cerdo desmechado", "Nachos au porc effiloché", 16.50)
    get_or_create_plato(cat_platos_ft.id, "Papas con costillas St-Louis", "Frites au côtes St-Louis", 18.50)
    get_or_create_plato(cat_platos_ft.id, "Papas con cerdo Bally", "Frites au porc Bally", 14.50)
    get_or_create_plato(cat_platos_ft.id, "Poutine clásica", "Poutine Classique", 12.50)
    get_or_create_plato(cat_platos_ft.id, "Poutine con cerdo desmechado", "Poutine au porc effiloché", 18.50)

    get_or_create_plato(cat_extras_ft.id, "Costillas St-Louis (extra)", "Côtes Ste Louis", 7.50)
    get_or_create_plato(cat_extras_ft.id, "Cerdo Bally (extra)", "Porc Bally", 7.50)
    get_or_create_plato(cat_extras_ft.id, "Queso (extra)", "Fromage", 6.50)

    get_or_create_plato(cat_entradas_ft.id, "Empanadas", "Empanadas", 4.00)

    get_or_create_plato(cat_postres_ft.id, "Churros de caramelo o chocolate", "Churros Caramel ou Chocolat", 10.00)

    print("Platos del Food Truck listos.")

    # ---------- CATEGORÍAS RESTO ----------
    cat_principales_resto = get_or_create_categoria("resto", "Platos Principales", "Plats Principaux", 1)
    cat_especial_resto = get_or_create_categoria("resto", "Plato Especial y Para Compartir", "Plat Spécial et À Partager", 2)
    cat_cantina_resto = get_or_create_categoria("resto", "Cantina", "Cantina", 3)
    cat_postres_resto = get_or_create_categoria("resto", "Postres", "Desserts", 4)

    print("Categorías del Resto listas.")

    get_or_create_plato(cat_principales_resto.id, "Steak & papas (8 oz)", "Steak & frites (8 oz)", 39.00)
    get_or_create_plato(cat_principales_resto.id, "Costillas al Néctar Negro (10 oz)", "Côtes au Nectar Noir 10oz", 31.00)
    get_or_create_plato(cat_principales_resto.id, "Pollo a la parrilla (8 oz)", "Poulet Grillé 8oz", 29.00)

    get_or_create_plato(cat_especial_resto.id, "Bife angosto a la parrilla (8 oz)", "Faux-filet grillé (8 oz)", 48.00)
    get_or_create_plato(cat_especial_resto.id, "Bife angosto a la parrilla (12 oz)", "Faux-filet grillé (12 oz)", 52.00)
    get_or_create_plato(cat_especial_resto.id, "El Festín del Barril - Experiencia del Chef", "Le Festin du Barril - Expérience du Chef", 85.00)

    get_or_create_plato(cat_cantina_resto.id, "Cerdo crujiente", "Porc Croustillant", 19.50)
    get_or_create_plato(cat_cantina_resto.id, "Choripán de Lujo", "Choripán de Luxe", 19.50)

    get_or_create_plato(cat_postres_resto.id, "Quesillo (flan de caramelo)", "Quesillo (flan au caramel)", 12.00)
    get_or_create_plato(cat_postres_resto.id, "Churros (6 piezas)", "Churros (6 morceaux)", 12.00)

    print("Platos del Resto listos.")