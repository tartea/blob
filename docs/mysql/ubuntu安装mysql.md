在ubuntu中，我们常用apt-get命令插件，其实，它也一直在更新相应的资源库，到目前为止，apt-get资源库中[mysql](https://cloud.tencent.com/product/cdb?from=10680)的最新版本为：mysql-5.7.29

因此，我们可以直接通过最新版本apt-get命令安装mysql57即可，避免手动安装的许多麻烦；

## 安装

### 卸载、清理残余

```shell
# 查看有没有已安装的依赖包
dpkg --list|grep mysql

# 卸载mysql-common
sudo apt-get remove mysql-common
sudo apt-get autoremove --purge mysql-server-5.0
```

### 安装myql

```shell
#更新apt-get，更新后将会使用最新资源库
sudo apt-get update

#安装MySQL:
sudo apt-get install mysql-server

#查看MySQL版本: 
mysql -V

#进入MySQL: 
mysql -u root -p
```

### 修改密码

由于mysql5.7没有password字段，密码存储在authentication_string字段中，password()方法还能用在mysql中执行下面语句修改密码

```shell
show databases;
use mysql;
update user set authentication_string=PASSWORD("123456") where user='root';
update user set plugin="mysql_native_password";
flush privileges;
exit;
```

### 修改数据库的编码格式

```shell
# 切换目录
/etc/mysql/mysql.conf.d

su vi mysqld.cnf
```

增加如下内容

```
[mysql]
default-character-set=utf8
[mysqld]
character_set_server=utf8
collation_server=utf8_general_ci
```

修改完以后重启mysql，重启命令`service mysql restart`

登录数据库，然后输入命令`show variables like 'character%'`就会发现编码格式都修改了