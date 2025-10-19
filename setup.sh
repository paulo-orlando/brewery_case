#!/bin/bash
# Setup script for local development

echo "🚀 Setting up Brewery Pipeline..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p data/bronze
mkdir -p data/silver
mkdir -p data/gold

# Run tests
echo "Running tests..."
pytest src/tests/ -v

echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To test the pipeline locally, run:"
echo "  python src/api/brewery_api.py ./data/raw"
echo "  python src/bronze/bronze_layer.py ./data/raw ./data/bronze"
echo "  python src/silver/silver_layer.py ./data/bronze ./data/silver"
echo "  python src/gold/gold_layer.py ./data/silver ./data/gold"
