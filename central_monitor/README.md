# Central Monitoring System

Project rieng de xay dung he thong giam sat tap trung cho thiet bi, server va service.

## Muc tieu

- Quan ly inventory thiet bi: AIBOX, camera, server, service.
- Ghi nhan event DOWN/RECOVERY/RESOURCE_ALERT.
- Tinh downtime, so lan mat ket noi, thiet bi chua clear.
- Lay du lieu tu email, SSH, Prometheus/Grafana hoac API noi bo.
- Dieu khien va truy van qua Telegram bot.

## Cau truc

```text
central_monitor/
  app.py
  config.py
  db.py
  models.py
  collectors/
  services/
  bot/
  docs/
```

## Chay thu

```bash
cd central_monitor
python app.py
```

## Huong phat trien

1. Hoan thien database inventory.
2. Them collector doc email alert.
3. Them Telegram bot menu.
4. Them collector SSH/Prometheus.
5. Them dashboard/API neu can.
