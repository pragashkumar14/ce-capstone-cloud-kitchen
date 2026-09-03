for count in 4 6 8 10 12; do
  echo "Sending $count errors..."
  for i in $(seq 1 $count); do
    curl -s -o /dev/null -w "%{http_code} " "https://pam-kitchen.online/demo/trigger-error?key=pamkitchen-demo-2026"
  done
  echo ""
  sleep 60
done
echo "Ramp complete"
