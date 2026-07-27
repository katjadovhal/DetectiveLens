"""Detective HQ shop catalogue — shared server-side price source of truth."""

HQ_SHOP_ITEMS = [
    {
        "id": "desk-dark",
        "name": "Dark Desk",
        "price": 400,
        "image": "DeskDark.png",
        "alt": "A dark wooden detective desk",
    },
    {
        "id": "desk-light",
        "name": "Light Desk",
        "price": 400,
        "image": "DeskLight.png",
        "alt": "A light wooden detective desk",
    },
    {
        "id": "chair-brown",
        "name": "Brown Chair",
        "price": 300,
        "image": "ChairBrown.png",
        "alt": "A brown detective chair",
    },
    {
        "id": "chair-green",
        "name": "Green Chair",
        "price": 300,
        "image": "ChairGreen.png",
        "alt": "A green detective chair",
    },
    {
        "id": "desk-decoration-1",
        "name": "Desk Decoration 1",
        "price": 200,
        "image": "DeskDecoration1.png",
        "alt": "Desk decoration set one",
    },
    {
        "id": "desk-decoration-2",
        "name": "Desk Decoration 2",
        "price": 200,
        "image": "DeskDecoration2.png",
        "alt": "Desk decoration set two",
    },
    {
        "id": "cabinet-green",
        "name": "Green Cabinet",
        "price": 400,
        "image": "CabinetGreen.png",
        "alt": "A green storage cabinet",
    },
    {
        "id": "cabinet-white",
        "name": "White Cabinet",
        "price": 400,
        "image": "CabinetWhite.png",
        "alt": "A white storage cabinet",
    },
]

HQ_SHOP_BY_ID = {item["id"]: item for item in HQ_SHOP_ITEMS}
