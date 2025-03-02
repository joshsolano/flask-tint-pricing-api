from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample pricing rules
def calculate_price(vehicle_year, vehicle_make, vehicle_model, tint_package, extras):
    base_price = 250  # Default price for tinting
    if "SUV" in vehicle_model.upper():
        base_price += 50  # SUVs cost more
    if "TRUCK" in vehicle_model.upper():
        base_price += 75  # Trucks cost more

    # Extra services
    if "Ceramic Tint" in extras:
        base_price += 100
    if "Tint Removal" in extras:
        base_price += 50

    return base_price

@app.route('/get-quote', methods=['POST'])
def get_quote():
    data = request.json
    price = calculate_price(
        data['vehicle_year'], 
        data['vehicle_make'], 
        data['vehicle_model'], 
        data['tint_package'], 
        data['extras']
    )
    return jsonify({"quote_price": price})

if __name__ == '__main__':
    app.run(port=5000)
