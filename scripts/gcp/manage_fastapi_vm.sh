#!/bin/bash
# Manage FastAPI VM (start/stop/status)

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"
INSTANCE_NAME="backtesting-api-vm"

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|ip|delete}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the VM"
    echo "  stop    - Stop the VM (save costs)"
    echo "  restart - Restart the VM"
    echo "  status  - Check VM status"
    echo "  logs    - View FastAPI logs"
    echo "  ip      - Get external IP"
    echo "  delete  - Delete VM completely"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

case $1 in
    start)
        echo "🚀 Starting VM..."
        gcloud compute instances start $INSTANCE_NAME --zone=$ZONE

        # Wait for VM to be ready
        echo "⏳ Waiting for VM to start..."
        sleep 20

        # Get IP
        EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

        echo "✅ VM started!"
        echo "API URL: http://$EXTERNAL_IP:8000"
        echo ""
        echo "Test health:"
        echo "  curl http://$EXTERNAL_IP:8000/health"
        ;;

    stop)
        echo "🛑 Stopping VM..."
        gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE
        echo "✅ VM stopped (no charges while stopped)"
        ;;

    restart)
        echo "🔄 Restarting VM..."
        gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE
        sleep 10
        gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
        echo "✅ VM restarted"
        ;;

    status)
        echo "📊 VM Status:"
        gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE \
            --format="table(name,status,machineType,networkInterfaces[0].accessConfigs[0].natIP)"

        echo ""
        echo "Service status:"
        gcloud compute ssh $INSTANCE_NAME --zone=$ZONE \
            --command='sudo systemctl status fastapi-backtest --no-pager'
        ;;

    logs)
        echo "📋 FastAPI Logs (Ctrl+C to exit):"
        gcloud compute ssh $INSTANCE_NAME --zone=$ZONE \
            --command='sudo journalctl -u fastapi-backtest -f'
        ;;

    ip)
        EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

        if [ -z "$EXTERNAL_IP" ]; then
            echo "❌ VM is not running or has no external IP"
            exit 1
        fi

        echo "External IP: $EXTERNAL_IP"
        echo "API URL: http://$EXTERNAL_IP:8000"
        echo "Docs: http://$EXTERNAL_IP:8000/docs"
        ;;

    delete)
        echo "⚠️  This will DELETE the VM completely!"
        read -p "Are you sure? (yes/no) " -r
        echo ""

        if [ "$REPLY" = "yes" ]; then
            echo "🗑️  Deleting VM..."
            gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet
            echo "✅ VM deleted"
        else
            echo "Cancelled"
        fi
        ;;

    *)
        usage
        ;;
esac
