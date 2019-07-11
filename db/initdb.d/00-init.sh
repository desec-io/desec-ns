# https://stackoverflow.com/questions/59895/can-a-bash-script-tell-which-directory-it-is-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for file in $DIR/*.sql.var; do
	envsubst < $file > $DIR/`basename $file .var`
done

cd $DIR

echo Getting pdns database dump from master ...
envsubst < my.cnf.var > my.cnf
mysqldump --defaults-file=./my.cnf --master-data=2 --databases pdns > 20-pdns.sql

echo Preparing CHANGE MASTER statement ...
echo -n "CHANGE MASTER TO MASTER_HOST='${DESECSTACK_DBMASTER}', MASTER_USER='${DESECSTACK_DBMASTER_USERNAME_replication}', MASTER_PASSWORD='${DESECSTACK_DBMASTER_PASSWORD_replication}', MASTER_SSL=1, MASTER_SSL_CA='/etc/ssl/private/ca.pem', MASTER_SSL_CERT='/etc/ssl/private/crt.pem', MASTER_SSL_KEY='/etc/ssl/private/key.pem', " > 21-pdns-CHANGEMASTER.sql
grep "^-- CHANGE MASTER TO " 20-pdns.sql | head -n1 | sed 's/^-- CHANGE MASTER TO //' >> 21-pdns-CHANGEMASTER.sql

echo Done, hope all went well.

cd -
