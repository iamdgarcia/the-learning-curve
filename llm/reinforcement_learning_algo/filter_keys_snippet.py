items = { 
    "Apple": 5, 
    "Banana": 3, 
    "Cherry": 8,
    "Avocado": 2
}
ks = ','.join([k for k in items.keys() if k[0] in {"A", "B"}])
print(f"resultkeyslist = {ks}")
