#!/bin/bash
# Manage GCP VMs (start/stop/status)

PROJECT_ID="rewts-quant-trading"
ZONE="us-central1-a"

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|ip|delete|list} [vm-name]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the VM"
    echo "  stop    - Stop the VM (save costs)"
    echo "  restart - Restart the VM"
    echo "  status  - Check VM status"
    echo "  logs    - View service logs (for backtesting VM)"
    echo "  ip      - Get external IP"
    echo "  delete  - Delete VM completely"
    echo "  list    - List all VMs"
    echo ""
    echo "VM Names:"
    echo "  rewts-training-spot   - Training VM (GPU)"
    echo "  backtesting-api-vm    - Backtesting API VM"
    echo ""
    echo "Examples:"
    echo "  $0 stop rewts-training-spot"
    echo "  $0 status backtesting-api-vm"
    echo "  $0 list"
    exit 1
}

# List VMs and auto-select if only one is running
list_vms() {
    echo "📋 Available VMs:"
    gcloud compute instances list --format="table(name,zone,status,machineType)" 2>/dev/null
}

# Get VM name from argument or auto-detect
get_vm_name() {
    local command=$1
    local vm_arg=$2

    if [ -n "$vm_arg" ]; then
        echo "$vm_arg"
        return 0
    fi

    # Check how many VMs exist (for start command, check all VMs)
    if [ "$command" = "start" ]; then
        all_vms=$(gcloud compute instances list --filter="status!=RUNNING" --format="value(name)" 2>/dev/null)
        vm_count=$(echo "$all_vms" | grep -v '^$' | wc -l | tr -d ' ')

        if [ "$vm_count" -eq 0 ]; then
            echo "" >&2
            echo "❌ No stopped VMs found" >&2
            echo "" >&2
            list_vms >&2
            return 1
        elif [ "$vm_count" -eq 1 ]; then
            echo "$all_vms"
            return 0
        else
            echo "" >&2
            echo "❌ Multiple stopped VMs found. Please specify which one:" >&2
            list_vms >&2
            echo "" >&2
            echo "Usage: $0 start [vm-name]" >&2
            return 1
        fi
    else
        # For other commands, check running VMs
        running_vms=$(gcloud compute instances list --filter="status=RUNNING" --format="value(name)" 2>/dev/null)
        vm_count=$(echo "$running_vms" | grep -v '^$' | wc -l | tr -d ' ')

        if [ "$vm_count" -eq 0 ]; then
            echo "" >&2
            echo "❌ No VMs are currently running" >&2
            echo "" >&2
            list_vms >&2
            return 1
        elif [ "$vm_count" -eq 1 ]; then
            echo "$running_vms"
            return 0
        else
            echo "" >&2
            echo "❌ Multiple VMs are running. Please specify which one:" >&2
            list_vms >&2
            echo "" >&2
            echo "Usage: $0 $command [vm-name]" >&2
            return 1
        fi
    fi
}

if [ $# -eq 0 ]; then
    usage
fi

COMMAND=$1

case $COMMAND in
    list)
        list_vms
        exit 0
        ;;

    start|stop|restart|status|logs|ip|delete)
        INSTANCE_NAME=$(get_vm_name "$COMMAND" "$2")

        if [ $? -ne 0 ] || [ -z "$INSTANCE_NAME" ]; then
            exit 1
        fi

        echo "🎯 Managing VM: $INSTANCE_NAME"
        echo ""
        ;;
    *)
        usage
        ;;
esac

case $COMMAND in
    start)
        echo "🚀 Starting VM..."
        if ! gcloud compute instances start $INSTANCE_NAME --zone=$ZONE; then
            echo "❌ Failed to start VM"
            exit 1
        fi

        # Wait for VM to be ready
        echo "⏳ Waiting for VM to start..."
        sleep 20

        # Get IP
        EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)

        echo "✅ VM started!"

        if [[ "$INSTANCE_NAME" == *"backtesting"* ]]; then
            echo "API URL: http://$EXTERNAL_IP:8000"
            echo ""
            echo "Test health:"
            echo "  curl http://$EXTERNAL_IP:8000/health"
        else
            echo "External IP: $EXTERNAL_IP"
            echo ""
            echo "SSH into VM:"
            echo "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
        fi
        ;;

    stop)
        echo "🛑 Stopping VM..."
        if ! gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE; then
            echo "❌ Failed to stop VM"
            exit 1
        fi
        echo "✅ VM stopped (no charges while stopped)"
        ;;

    restart)
        echo "🔄 Restarting VM..."
        if ! gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE; then
            echo "❌ Failed to stop VM"
            exit 1
        fi
        sleep 10
        if ! gcloud compute instances start $INSTANCE_NAME --zone=$ZONE; then
            echo "❌ Failed to start VM"
            exit 1
        fi
        echo "✅ VM restarted"
        ;;

    status)
        echo "📊 VM Status:"
        gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE \
            --format="table(name,status,machineType,networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null

        # Only check service status for backtesting VM
        if [[ "$INSTANCE_NAME" == *"backtesting"* ]]; then
            echo ""
            echo "Service status:"
            gcloud compute ssh $INSTANCE_NAME --zone=$ZONE \
                --command='sudo systemctl status fastapi-backtest --no-pager' 2>/dev/null || echo "⚠️  Could not check service status"
        fi
        ;;

    logs)
        if [[ "$INSTANCE_NAME" == *"backtesting"* ]]; then
            echo "📋 FastAPI Logs (Ctrl+C to exit):"
            gcloud compute ssh $INSTANCE_NAME --zone=$ZONE \
                --command='sudo journalctl -u fastapi-backtest -f'
        else
            echo "📋 System Logs (Ctrl+C to exit):"
            gcloud compute ssh $INSTANCE_NAME --zone=$ZONE \
                --command='sudo journalctl -f'
        fi
        ;;

    ip)
        EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)

        if [ -z "$EXTERNAL_IP" ]; then
            echo "❌ VM is not running or has no external IP"
            exit 1
        fi

        echo "External IP: $EXTERNAL_IP"

        if [[ "$INSTANCE_NAME" == *"backtesting"* ]]; then
            echo "API URL: http://$EXTERNAL_IP:8000"
            echo "Docs: http://$EXTERNAL_IP:8000/docs"
        else
            echo ""
            echo "SSH:"
            echo "  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
        fi
        ;;

    delete)
        echo "⚠️  This will DELETE $INSTANCE_NAME completely!"
        read -p "Are you sure? (yes/no) " -r
        echo ""

        if [ "$REPLY" = "yes" ]; then
            echo "🗑️  Deleting VM..."
            if ! gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet; then
                echo "❌ Failed to delete VM"
                exit 1
            fi
            echo "✅ VM deleted"
        else
            echo "Cancelled"
        fi
        ;;
esac
