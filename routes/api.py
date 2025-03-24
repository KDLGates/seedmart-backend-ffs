from flask import Blueprint, request, jsonify
from models.models import db, Seed, SeedPrice
from services.market import MarketService
from datetime import datetime, timedelta
from sqlalchemy import desc
from flask_jwt_extended import jwt_required

api = Blueprint('api', __name__)

@api.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# Public endpoints for market data - no authentication required
@api.route('/seeds', methods=['GET'])
def get_seeds():
    seeds = Seed.query.all()
    return jsonify([seed.to_dict() for seed in seeds])

@api.route('/seeds/<int:id>', methods=['GET'])
def get_seed(id):
    seed = Seed.query.get_or_404(id)
    return jsonify(seed.to_dict())

@api.route('/seeds/<int:seed_id>/prices', methods=['GET'])
def get_seed_prices(seed_id):
    """Get price history for a specific seed"""
    timeframe = request.args.get('timeframe', '1w')
    try:
        limit = int(request.args.get('limit')) if request.args.get('limit') else None
    except ValueError:
        limit = None
    
    price_history = MarketService.get_price_history(seed_id, timeframe, limit)
    return jsonify(price_history)

@api.route('/seeds/<int:id>/latest-price', methods=['GET'])
def get_seed_latest_price(id):
    # Check if seed exists
    seed = Seed.query.get_or_404(id)
    
    # Get the latest price entry
    latest_price = SeedPrice.query.filter_by(seed_id=id).order_by(desc(SeedPrice.recorded_at)).first()
    
    if not latest_price:
        return jsonify({"error": "No price history available for this seed"}), 404
        
    return jsonify(latest_price.to_dict())

@api.route('/market/summary', methods=['GET'])
def get_market_summary():
    """Get market summary with current prices and statistics"""
    market_data = MarketService.get_market_summary()
    return jsonify(market_data)

# Admin endpoints that require authentication
@api.route('/market/update', methods=['POST'])
@jwt_required()
def update_market():
    """Update all seed prices - should be called by a scheduled task"""
    try:
        updates = MarketService.update_seed_prices()
        return jsonify({'success': True, 'updates': updates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/seeds', methods=['POST'])
@jwt_required()
def create_seed():
    data = request.json
    new_seed = Seed(
        name=data['name'],
        species=data.get('species'),
        quantity=data.get('quantity', 0),
        price=data.get('price'),
        description=data.get('description')
    )
    db.session.add(new_seed)
    db.session.commit()
    
    # Add initial price entry
    if new_seed.price:
        new_price = SeedPrice(
            seed_id=new_seed.id,
            price=new_seed.price,
            volume=new_seed.quantity,
            recorded_at=datetime.now()
        )
        db.session.add(new_price)
        db.session.commit()
    
    return jsonify(new_seed.to_dict()), 201

@api.route('/seeds/<int:id>', methods=['PUT'])
@jwt_required()
def update_seed(id):
    seed = Seed.query.get_or_404(id)
    data = request.json
    
    seed.name = data.get('name', seed.name)
    seed.species = data.get('species', seed.species)
    seed.quantity = data.get('quantity', seed.quantity)
    
    # Update price if provided
    if 'price' in data and data['price'] != seed.price:
        seed.price = data['price']
        
        # Add new price entry
        new_price = SeedPrice(
            seed_id=seed.id,
            price=seed.price,
            volume=seed.quantity,
            recorded_at=datetime.now()
        )
        db.session.add(new_price)
        
    seed.description = data.get('description', seed.description)
    
    db.session.commit()
    return jsonify(seed.to_dict())

@api.route('/seeds/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_seed(id):
    seed = Seed.query.get_or_404(id)
    db.session.delete(seed)
    db.session.commit()
    return jsonify({"message": "Seed deleted"}), 200