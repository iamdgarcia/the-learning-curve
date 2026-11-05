# Sample RL Algorithms snippet with filtering

items = { 
    "Apple": 5, 
    "Banana": 3, 
    "Cherry": 8,
    "Avocado": 2
}

def kind(name: str):
    return name[0].upper() if len(name) > 0 else "Unknown"

# Filter items where kind(x[0]) in {A, B}
filtered_items = list(filter(lambda x: kind(x[0]) in {"A", "B"}, items.items()))

print("Filtered items:", filtered_items)
print("Keys as list:", list(dict.fromkeys(filtered_items)))
