#!/bin/bash

# RT Prediction API - Complete Molgpu Deployment & Management
# This script handles deployment and provides management commands

# Function to show usage
show_usage() {
    echo "Usage: $0 {deploy|start|stop|restart|status|logs}"
    echo ""
    echo "Commands:"
    echo "  deploy  - Complete deployment (environment + service)"
    echo "  start   - Start the API service"
    echo "  stop    - Stop the API service"
    echo "  restart - Restart the API service"
    echo "  status  - Show service status"
    echo "  logs    - Show service logs"
}

# Function to deploy
deploy() {
    echo "🚀 RT Prediction API - Complete Molgpu Deployment"
    echo "=================================================="

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
       echo "❌ This script should not be run as root"
       exit 1
    fi

    # Get current user and directory
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)
    echo "👤 Deploying as user: $CURRENT_USER"
    echo "📁 Current directory: $CURRENT_DIR"

    # Create service file dynamically
    echo "📝 Creating service file..."
    cat > rtpred-api.service << EOF
[Unit]
Description=RT Prediction API Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$ENV_PATH/bin
ExecStart=$ENV_PATH/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Make script executable
    chmod +x setup_molgpu_env.sh

    # Run environment setup
    echo "🔧 Setting up conda environment..."
    ./setup_molgpu_env.sh

    if [ $? -ne 0 ]; then
        echo "❌ Environment setup failed!"
        exit 1
    fi

    # Test environment
    echo "🧪 Testing environment..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate lcgenv

    if ! command -v uvicorn &> /dev/null; then
        echo "❌ uvicorn not found in lcgenv environment!"
        exit 1
    fi

    echo "✅ Environment test passed!"

    # Start service
    echo "🚀 Starting RT Prediction API service..."
    sudo cp rtpred-api.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable rtpred-api.service
    sudo systemctl start rtpred-api.service

    # Wait and test
    echo "⏳ Waiting for service to start..."
    sleep 5

    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is responding!"
        echo ""
        echo "🎉 Deployment successful!"
        echo "========================"
        echo "API URL: http://molgpu:8000"
        echo "Health check: curl http://molgpu:8000/health"
        echo "API docs: http://molgpu:8000/docs"
        echo ""
        echo "📋 Management: $0 {start|stop|restart|status|logs}"
    else
        echo "❌ API is not responding!"
        echo "📋 Check logs: $0 logs"
        exit 1
    fi
}

# Function to manage service
manage_service() {
    case "$1" in
        start)
            echo "Starting RT Prediction API..."
            sudo systemctl start rtpred-api.service
            sudo systemctl status rtpred-api.service
            ;;
        stop)
            echo "Stopping RT Prediction API..."
            sudo systemctl stop rtpred-api.service
            ;;
        restart)
            echo "Restarting RT Prediction API..."
            sudo systemctl restart rtpred-api.service
            sudo systemctl status rtpred-api.service
            ;;
        status)
            echo "RT Prediction API Status:"
            sudo systemctl status rtpred-api.service
            ;;
        logs)
            echo "RT Prediction API Logs:"
            sudo journalctl -u rtpred-api.service -f
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    start|stop|restart|status|logs)
        manage_service "$1"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
