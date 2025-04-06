"""
Example file with intentional issues to demonstrate bolor's code analysis capabilities.
"""

# Missing docstrings in functions
def calculate_sum(a, b):
    return a + b

# Potentially undefined variable
def process_data(data):
    result = []
    for item in data:
        processed_item = _transform(item)  # _transform is not defined
        result.append(processed_item)
    return result

# Complex expression that could be simplified
def calculate_complex_value(x, y, z):
    return x + y * z / 2 + (x * y) / (z + 1) - (x / y) * z + (y ** 2) - (z % x) + (x if y > z else z)

# Code with inefficient implementation
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates

# Function that could benefit from a generator
def get_large_list():
    result = []
    for i in range(1000000):
        result.append(i * i)
    return result

if __name__ == "__main__":
    # Example usage
    print(calculate_sum(5, 3))
    
    try:
        data = [1, 2, 3, 4, 5]
        processed = process_data(data)
        print(processed)
    except NameError as e:
        print(f"Error: {e}")
    
    print(calculate_complex_value(2, 3, 4))
    
    items = [1, 2, 3, 2, 4, 5, 4, 6]
    print(find_duplicates(items))
