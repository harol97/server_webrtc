echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
sudo systemctl start redis-server
uv run --env-file .env -- uvicorn main:app
