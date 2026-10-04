#!/bin/bash
set -e

mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld

if [ ! -d /var/lib/mysql/mysql ]; then
  mariadb-install-db --user=mysql --datadir=/var/lib/mysql >/dev/null
fi

mysqld --user=mysql --bind-address=127.0.0.1 --port=3306 --skip-log-bin &
MYSQL_PID=$!
trap 'kill $MYSQL_PID 2>/dev/null || true' EXIT

for i in $(seq 1 60); do
  if mariadb-admin --protocol=socket -uroot ping >/dev/null 2>&1; then break; fi
  sleep 1
done

mariadb --protocol=socket -uroot <<'SQL'
CREATE USER IF NOT EXISTS 'campro'@'127.0.0.1' IDENTIFIED BY 'campro_deploy_2026';
ALTER USER 'campro'@'127.0.0.1' IDENTIFIED BY 'campro_deploy_2026';
GRANT ALL PRIVILEGES ON *.* TO 'campro'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

export Database__Server=127.0.0.1
export Database__Port=3306
export Database__Database=campro_csharp
export Database__User=campro
export Database__Password=campro_deploy_2026

cd /app/publish
exec dotnet CamPro.Web.dll
