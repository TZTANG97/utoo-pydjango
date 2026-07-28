# 139 测试服：从单实例 `/opt/utoo` 迁到红绿双实例

目标机：`139.129.26.211`  
对齐：[`deploy/README.md`](README.md)、[`deploy/systemd/*-{blue,green}.service.example`](systemd/)、[`deploy/nginx/`](nginx/)

**与工厂 EMKU 隔离**：不要动 `/opt/emku-*`、`emku_upstream_*`、`emku-switch-*`。

## 迁前状态（当前）

- 代码：`/opt/utoo`
- systemd：`qd-order` `qd-payment` `qd-admin-asset` `qd-admin-platform` `qd-gateway`（无后缀）
- 端口：18082 / 18084 / 18090 / 18091 / 18083
- 静态：`/var/www/utoo-web`
- Python：`/opt/utoo/.python`（可选，Miniconda 独立解释器）

## 步骤概览

1. 备份  
2. 共享配置抽到 `/opt/utoo/config`  
3. `/opt/utoo` → `/opt/utoo-blue`（保留 180xx）  
4. 安装并启用 `*-blue` unit，停用旧无后缀 unit  
5. 准备 `/opt/utoo-green`（181xx）  
6. 安装 upstream + 切流脚本  
7. 验收  

---

### 1. 备份

```bash
sudo cp -a /etc/systemd/system/qd-order.service /root/qd-order.service.bak.$(date +%Y%m%d) || true
# 同理备份其余 qd-*.service
sudo mkdir -p /root/utoo-backup
sudo tar -czf /root/utoo-backup/opt-utoo-$(date +%Y%m%d).tgz -C /opt utoo
```

### 2. 共享配置目录

各服务 settings 读取 `BASE_DIR.parent/config/shared-database.env`，故每槽需要 `config/shared-database.env`。

```bash
sudo mkdir -p /opt/utoo/config
# 若文件已在 /opt/utoo/config/shared-database.env，可跳过复制
# 否则从旧位置挪过来：
# sudo mv /opt/utoo/config/shared-database.env /opt/utoo/config/  # 已在则不动

sudo chown -R deploy:deploy /opt/utoo
```

### 3. 将现网迁为 blue

短暂停服窗口（建议低峰）：

```bash
sudo systemctl stop qd-order qd-payment qd-admin-asset qd-admin-platform qd-gateway

# 保留 /opt/utoo/config 与 /opt/utoo/.python（若有），把业务树迁到 blue
sudo mkdir -p /opt/utoo-blue
# 若 /opt/utoo 下已是业务目录，可整体改名再拆出 config：
sudo mv /opt/utoo /opt/utoo-blue-tmp
sudo mkdir -p /opt/utoo/config
# 从 tmp 取出共享配置与独立 Python
if [ -f /opt/utoo-blue-tmp/config/shared-database.env ]; then
  sudo cp -a /opt/utoo-blue-tmp/config/shared-database.env /opt/utoo/config/
fi
if [ -d /opt/utoo-blue-tmp/.python ]; then
  sudo mv /opt/utoo-blue-tmp/.python /opt/utoo/.python
fi
sudo mv /opt/utoo-blue-tmp /opt/utoo-blue

# 槽内 config 指向共享文件
sudo mkdir -p /opt/utoo-blue/config
sudo ln -sfn /opt/utoo/config/shared-database.env /opt/utoo-blue/config/shared-database.env
sudo chown -R deploy:deploy /opt/utoo /opt/utoo-blue
```

> 若你更习惯「先 rsync 到 `/opt/utoo-blue` 再删旧目录」，效果相同；关键是最终路径与端口符合蓝槽表。

### 4. 安装 blue systemd，停用旧 unit

在仓库机器上把 `deploy/systemd/*-blue.service.example` 拷到服务器，或：

```bash
cd /opt/utoo-blue/deploy/systemd   # 若代码树内已有；否则从本机 scp
for u in qd-order-blue qd-payment-blue qd-admin-asset-blue qd-admin-platform-blue qd-gateway-blue; do
  sudo cp "${u}.service.example" "/etc/systemd/system/${u}.service"
done
sudo systemctl daemon-reload
sudo systemctl disable --now qd-order qd-payment qd-admin-asset qd-admin-platform qd-gateway || true
sudo systemctl enable --now qd-order-blue qd-payment-blue qd-admin-asset-blue qd-admin-platform-blue qd-gateway-blue

ss -lntp | grep -E '18082|18083|18084|18090|18091'
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18083/api/
```

### 5. 准备 green（可稍后；首次 CI 也会往空闲槽灌代码）

```bash
sudo mkdir -p /opt/utoo-green
sudo rsync -a --exclude '.venv' /opt/utoo-blue/ /opt/utoo-green/
# 每服务单独建 venv（用 /opt/utoo/.python/bin/python 若存在）
PY=/opt/utoo/.python/bin/python
command -v "$PY" >/dev/null || PY=python3

for d in qd_svc_order qd_svc_payment qd_svc_admin_asset qd_svc_admin_platform qd_test_server_django; do
  cd /opt/utoo-green/$d
  rm -rf .venv
  sudo -u deploy "$PY" -m venv .venv
  sudo -u deploy .venv/bin/pip install -U pip
  sudo -u deploy .venv/bin/pip install -r requirements.txt gunicorn
  sudo -u deploy .venv/bin/pip install -e /opt/utoo-green/qd_libs_common
done

# 改绿槽端口（示例：用 sed；请核对 .env）
sudo sed -i 's/18082/18182/g; s/18084/18184/g; s/18090/18190/g; s/18091/18191/g; s/18083/18183/g' \
  /opt/utoo-green/qd_svc_order/.env \
  /opt/utoo-green/qd_svc_payment/.env \
  /opt/utoo-green/qd_svc_admin_asset/.env \
  /opt/utoo-green/qd_svc_admin_platform/.env \
  /opt/utoo-green/qd_test_server_django/.env

sudo mkdir -p /opt/utoo-green/config
sudo ln -sfn /opt/utoo/config/shared-database.env /opt/utoo-green/config/shared-database.env
sudo chown -R deploy:deploy /opt/utoo-green

# 安装 green unit
for u in qd-order-green qd-payment-green qd-admin-asset-green qd-admin-platform-green qd-gateway-green; do
  sudo cp "/path/to/repo/deploy/systemd/${u}.service.example" "/etc/systemd/system/${u}.service"
done
sudo systemctl daemon-reload
sudo systemctl enable qd-order-green qd-payment-green qd-admin-asset-green qd-admin-platform-green qd-gateway-green
# 可先 start 验端口，不切 Nginx 则对外仍走蓝
sudo systemctl start qd-order-green qd-payment-green qd-admin-asset-green qd-admin-platform-green qd-gateway-green
ss -lntp | grep -E '18182|18183|18184|18190|18191'
```

### 6. Upstream + 切流脚本

```bash
sudo cp deploy/nginx/utoo_upstream_server.conf.example /usr/local/nginx/conf/utoo_upstream_server.conf
# 确认内容为：server 127.0.0.1:18083;

sudo cp deploy/nginx/utoo-switch-active.sh.example /usr/local/sbin/utoo-switch-active.sh
sudo chmod 755 /usr/local/sbin/utoo-switch-active.sh

# 试切（确认后再切回 18083）
sudo /usr/local/sbin/utoo-switch-active.sh 18183
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18183/api/
sudo /usr/local/sbin/utoo-switch-active.sh 18083
```

域名 `uat.utoodev.laide.tech` 的 server 块见 `deploy/nginx/uat.utoodev.laide.tech.conf.example`（证书与 DNS 就绪后再 include，勿改现有其它站点）。

### 7. 验收清单

- [ ] `systemctl is-active qd-*-blue` 全 active  
- [ ] 蓝端口 180xx 监听；绿若已启则 181xx 监听  
- [ ] `cat /usr/local/nginx/conf/utoo_upstream_server.conf` 指向期望网关  
- [ ] `/var/www/utoo-web/index.html` 存在  
- [ ] 旧无后缀 `qd-order` 等已 disable  

之后日常发版走 GitLab `utoo-windows` Pipeline（空闲槽 → health → switch → 静态）。
